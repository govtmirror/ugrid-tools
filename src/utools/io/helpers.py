import os
from collections import deque, OrderedDict
from copy import copy

import fiona
import numpy as np
from addict import Dict
from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from shapely.geometry.base import BaseMultipartGeometry
from shapely.geometry.polygon import orient

from geom_cabinet import GeomCabinetIterator
from mpi import MPI_RANK, create_sections, MPI_COMM, hgather, vgather, MPI_SIZE, dgather
from spatial_index import SpatialIndex
from utools.constants import UgridToolsConstants


def convert_multipart_to_singlepart(path_in, path_out, new_uid_name=UgridToolsConstants.LINK_ATTRIBUTE_NAME, start=0):
    """
    Convert a vector GIS file from multipart to singlepart geometries. The function copies all attributes and
    maintains the coordinate system.

    :param str path_in: Path to the input file containing multipart geometries.
    :param str path_out: Path to the output file.
    :param str new_uid_name: Use this name as the default for the new unique identifier.
    :param int start: Start value for the new unique identifier.
    """

    with fiona.open(path_in) as source:
        len_source = len(source)
        source.meta['schema']['properties'][new_uid_name] = 'int'
        with fiona.open(path_out, mode='w', **source.meta) as sink:
            for ctr, record in enumerate(source, start=1):
                geom = shape(record['geometry'])
                if isinstance(geom, BaseMultipartGeometry):
                    for element in geom:
                        record['properties'][new_uid_name] = start
                        record['geometry'] = mapping(element)
                        sink.write(record)
                        start += 1
                else:
                    record['properties'][new_uid_name] = start
                    sink.write(record)
                    start += 1


def get_coordinates_list_and_update_n_coords(record, n_coords):
    geom = record['geom']
    if isinstance(geom, MultiPolygon):
        itr = iter(geom)
    else:
        itr = [geom]
    coordinates_list = []
    for element in itr:
        # Counter-clockwise orientations required by clients such as ESMF Mesh regridding.
        exterior = element.exterior
        if not exterior.is_ccw:
            coords = list(exterior.coords)[::-1]
        else:
            coords = list(exterior.coords)
        current_coordinates = np.array(coords)
        # Assert last coordinate is repeated for each polygon.
        assert current_coordinates[0].tolist() == current_coordinates[-1].tolist()
        # Remove this repeated coordinate.
        current_coordinates = current_coordinates[0:-1, :]
        coordinates_list.append(current_coordinates)
        n_coords += current_coordinates.shape[0]

    return coordinates_list, n_coords


def get_coordinate_dict_variables(cdict, n_coords, polygon_break_value=None):
    polygon_break_value = polygon_break_value or UgridToolsConstants.POLYGON_BREAK_VALUE
    dtype_int = np.int32
    face_nodes = np.zeros(len(cdict), dtype=object)
    idx_start = 0
    for idx_face_nodes, coordinates_list in enumerate(cdict.itervalues()):
        if idx_face_nodes == 0:
            coordinates = np.zeros((n_coords, 2), dtype=coordinates_list[0].dtype)
            edge_nodes = np.zeros_like(coordinates, dtype=dtype_int)
        for ctr, coordinates_element in enumerate(coordinates_list):
            shape_coordinates_row = coordinates_element.shape[0]
            idx_stop = idx_start + shape_coordinates_row

            new_face_nodes = np.arange(idx_start, idx_stop, dtype=dtype_int)
            edge_nodes[idx_start: idx_stop, :] = get_edge_nodes(new_face_nodes)
            if ctr == 0:
                face_nodes_element = new_face_nodes
            else:
                face_nodes_element = np.hstack((face_nodes_element, polygon_break_value))
                face_nodes_element = np.hstack((face_nodes_element, new_face_nodes))
            coordinates[idx_start:idx_stop, :] = coordinates_element
            idx_start += shape_coordinates_row
        face_nodes[idx_face_nodes] = face_nodes_element.astype(dtype_int)
    return face_nodes, coordinates, edge_nodes


def get_edge_nodes(face_nodes):
    first = face_nodes.reshape(-1, 1)
    second = first + 1
    edge_nodes = np.hstack((first, second))
    edge_nodes[-1, 1] = edge_nodes[0, 0]
    return edge_nodes


def get_variables(gm, use_ragged_arrays=False, with_connectivity=True):
    """
    :param gm: The geometry manager containing geometries to convert to mesh variables.
    :type gm: :class:`pyugrid.flexible_mesh.helpers.GeometryManager`
    :param pack: If ``True``, de-deduplicate shared coordinates.
    :type pack: bool
    :returns: A tuple of arrays with index locations corresponding to:

    ===== ================ =============================
    Index Name             Type
    ===== ================ =============================
    0     face_nodes       :class:`numpy.ma.MaskedArray`
    1     face_edges       :class:`numpy.ma.MaskedArray`
    2     edge_nodes       :class:`numpy.ndarray`
    3     node_x           :class:`numpy.ndarray`
    4     node_y           :class:`numpy.ndarray`
    5     face_links       :class:`numpy.ndarray`
    6     face_ids         :class:`numpy.ndarray`
    7     face_coordinates :class:`numpy.ndarray`
    ===== ================ =============================

    Information on individual variables may be found here: https://github.com/ugrid-conventions/ugrid-conventions/blob/9b6540405b940f0a9299af9dfb5e7c04b5074bf7/ugrid-conventions.md#2d-flexible-mesh-mixed-triangles-quadrilaterals-etc-topology

    :rtype: tuple (see table for array types)
    :raises: ValueError
    """
    # tdk: update doc
    if len(gm) < MPI_SIZE:
        raise ValueError('The number of geometries must be greater than or equal to the number of processes.')

    result = get_face_variables(gm, with_connectivity=with_connectivity)

    if MPI_RANK == 0:
        face_links, nmax_face_nodes, face_ids, face_coordinates, cdict, n_coords, face_areas = result
    else:
        return

    pbv = UgridToolsConstants.POLYGON_BREAK_VALUE
    face_nodes, coordinates, edge_nodes = get_coordinate_dict_variables(cdict, n_coords, polygon_break_value=pbv)
    face_edges = face_nodes
    face_ids = np.array(cdict.keys(), dtype=np.int32)

    if not use_ragged_arrays:
        new_arrays = []
        for a in (face_links, face_nodes, face_edges):
            new_arrays.append(get_rectangular_array_from_object_array(a, (a.shape[0], nmax_face_nodes)))
        face_links, face_nodes, face_edges = new_arrays

    return face_nodes, face_edges, edge_nodes, coordinates, face_links, face_ids, face_coordinates, face_areas


def get_rectangular_array_from_object_array(target, shape):
    new_face_links = np.ma.array(np.zeros(shape, dtype=target[0].dtype), mask=True)
    for idx, f in enumerate(target):
        new_face_links[idx, 0:f.shape[0]] = f
    face_links = new_face_links
    assert (face_links.ndim == 2)
    return face_links


def iter_touching(si, gm, shapely_object):
    select_uid = list(si.iter_rtree_intersection(shapely_object))
    select_uid.sort()
    for uid_target, record_target in gm.iter_records(return_uid=True, select_uid=select_uid):
        if shapely_object.touches(record_target['geom']):
            yield uid_target


def get_face_variables(gm, with_connectivity=True):
    n_face = len(gm)

    if MPI_RANK == 0:
        sections = create_sections(n_face)
    else:
        sections = None

    section = MPI_COMM.scatter(sections, root=0)

    # Create a spatial index to find touching faces.
    if with_connectivity:
        si = gm.get_spatial_index()

    face_ids = np.zeros(section[1] - section[0], dtype=np.int32)
    assert face_ids.shape[0] > 0

    face_links = {}
    max_face_nodes = 0
    face_coordinates = deque()
    face_areas = deque()

    cdict = OrderedDict()
    n_coords = 0

    for ctr, (uid_source, record_source) in enumerate(gm.iter_records(return_uid=True, slice=section)):
        coordinates_list, n_coords = get_coordinates_list_and_update_n_coords(record_source, n_coords)
        cdict[uid_source] = coordinates_list

        face_ids[ctr] = uid_source
        ref_object = record_source['geom']

        # Get representative points for each polygon.
        face_coordinates.append(np.array(ref_object.representative_point()))
        face_areas.append(ref_object.area)

        # For polygon geometries the first coordinate is repeated at the end of the sequence. UGRID clients do not want
        # repeated coordinates (i.e. ESMF).
        try:
            ncoords = len(ref_object.exterior.coords) - 1
        except AttributeError:
            # Likely a multipolygon...
            ncoords = sum([len(e.exterior.coords) - 1 for e in ref_object])
            # A -1 flag will be placed between elements.
            ncoords += (len(ref_object) - 1)
        if ncoords > max_face_nodes:
            max_face_nodes = ncoords

        if with_connectivity:
            touching = deque()
            for uid_target in iter_touching(si, gm, ref_object):
                # If the objects only touch they are neighbors and may share nodes.
                touching.append(uid_target)
            # If nothing touches the faces, indicate this with a flag value.
            if len(touching) == 0:
                touching.append(-1)
            face_links[uid_source] = touching

    face_ids = MPI_COMM.gather(face_ids, root=0)
    max_face_nodes = MPI_COMM.gather(max_face_nodes, root=0)
    face_links = MPI_COMM.gather(face_links, root=0)
    face_coordinates = MPI_COMM.gather(np.array(face_coordinates), root=0)
    cdict = MPI_COMM.gather(cdict, root=0)
    n_coords = MPI_COMM.gather(n_coords, root=0)
    face_areas = MPI_COMM.gather(np.array(face_areas), root=0)

    if MPI_RANK == 0:
        face_ids = hgather(face_ids)
        face_coordinates = vgather(face_coordinates)
        cdict = dgather(cdict)
        n_coords = sum(n_coords)
        face_areas = hgather(face_areas)

        max_face_nodes = max(max_face_nodes)

        if with_connectivity:
            face_links = get_mapped_face_links(face_ids, face_links)
        else:
            face_links = None

        return face_links, max_face_nodes, face_ids, face_coordinates, cdict, n_coords, face_areas


def get_mapped_face_links(face_ids, face_links):
    """
    :param face_ids: Vector of unique, integer face identifiers.
    :type face_ids: :class:`numpy.ndarray`
    :param face_links: List of dictionaries mapping face unique identifiers to neighbor face unique identifiers.
    :type face_links: list
    :returns: A numpy object array with slots containing numpy integer vectors with values equal to neighbor indices.
    :rtype: :class:`numpy.ndarray`
    """

    face_links = dgather(face_links)
    new_face_links = np.zeros(len(face_links), dtype=object)
    for idx, e in enumerate(face_ids.flat):
        to_fill = np.zeros(len(face_links[e]), dtype=np.int32)
        for idx_f, f in enumerate(face_links[e]):
            # This flag indicates nothing touches the faces. Do not search for this value in the face identifiers.
            if f == -1:
                to_fill_value = f
            # Search for the index location of the face identifier.
            else:
                to_fill_value = np.where(face_ids == f)[0][0]
            to_fill[idx_f] = to_fill_value
        new_face_links[idx] = to_fill
    return new_face_links


def flexible_mesh_to_fiona(out_path, face_nodes, node_x, node_y, crs=None, driver='ESRI Shapefile',
                           indices_to_load=None, face_uid=None):
    if face_uid is None:
        properties = {}
    else:
        properties = {face_uid.name: 'int'}

    schema = {'geometry': 'Polygon', 'properties': properties}
    with fiona.open(out_path, 'w', driver=driver, crs=crs, schema=schema) as f:
        for feature in iter_records(face_nodes, node_x, node_y, indices_to_load=indices_to_load, datasets=[face_uid],
                                    polygon_break_value=UgridToolsConstants.POLYGON_BREAK_VALUE):
            feature['properties'][face_uid.name] = int(feature['properties'][face_uid.name])
            f.write(feature)
    return out_path


def iter_records(face_nodes, node_x, node_y, indices_to_load=None, datasets=None, shapely_only=False,
                 polygon_break_value=None):
    if indices_to_load is None:
        feature_indices = range(face_nodes.shape[0])
    else:
        feature_indices = indices_to_load

    for feature_idx in feature_indices:
        try:
            current_face_node = face_nodes[feature_idx, :]
        except IndexError:
            # Likely an object array.
            assert face_nodes.dtype == object
            current_face_node = face_nodes[feature_idx]

        try:
            nodes = current_face_node.compressed()
        except AttributeError:
            # Likely not a masked array.
            nodes = current_face_node.flatten()

        # Construct the geometry object by collecting node coordinates using indices stored in "nodes".
        if polygon_break_value is not None and polygon_break_value in nodes:
            itr = get_split_array(nodes, polygon_break_value)
            has_multipart = True
        else:
            itr = [nodes]
            has_multipart = False
        polygons = []
        for sub in itr:
            coordinates = [(node_x[ni], node_y[ni]) for ni in sub.flat]
            polygons.append(Polygon(coordinates))
        if has_multipart:
            polygon = MultiPolygon(polygons)
        else:
            polygon = polygons[0]

        # Collect properties if datasets are passed.
        properties = OrderedDict()
        if datasets is not None:
            for ds in datasets:
                properties[ds.name] = ds.data[feature_idx]
        feature = {'id': feature_idx, 'properties': properties}

        # Add coordinates or shapely objects depending on parameters.
        if shapely_only:
            feature['geom'] = polygon
        else:
            feature['geometry'] = mapping(polygon)

        yield feature


def create_rtree_file(gm, path):
    """
    :param gm: Target geometries to index.
    :type gm: :class:`pyugrid.flexible_mesh.helpers.GeometryManager`
    :param path: Output path for the serialized spatial index. See http://toblerity.org/rtree/tutorial.html#serializing-your-index-to-a-file.
    """

    si = SpatialIndex(path=path)
    for uid, record in gm.iter_records(return_uid=True):
        si.add(uid, record['geom'])


class GeometryManager(object):
    """
    Provides iteration, validation, and other management routines for collecting vector geometries from record lists or
    flat files.
    """

    def __init__(self, name_uid, path=None, records=None, path_rtree=None, allow_multipart=False, node_threshold=None):
        if path_rtree is not None:
            assert os.path.exists(path_rtree + '.idx')

        self.path = path
        self.path_rtree = path_rtree
        self.name_uid = name_uid
        self.records = copy(records)
        self.allow_multipart = allow_multipart
        self.node_threshold = node_threshold

        self._has_provided_records = False if records is None else True

    def __len__(self):
        if self.records is None:
            ret = len(GeomCabinetIterator(path=self.path))
        else:
            ret = len(self.records)
        return ret

    def get_spatial_index(self):
        si = SpatialIndex(path=self.path_rtree)
        # Only add new records to the index if we are working in-memory.
        if self.path_rtree is None:
            for uid, record in self.iter_records(return_uid=True):
                si.add(uid, record['geom'])
        return si

    def iter_records(self, return_uid=False, select_uid=None, slice=None):
        # Use records attached to the object or load records from source data.
        to_iter = self.records or self._get_records_(select_uid=select_uid, slice=slice)

        if self.records is not None and slice is not None:
            to_iter = to_iter[slice[0]:slice[1]]

        for ctr, record in enumerate(to_iter):
            if self._has_provided_records and 'geom' not in record:
                record['geom'] = shape(record['geometry'])
                # Only use the geometry objects from here. Maintaining the list of coordinates is superfluous.
                record.pop('geometry')
            self._validate_record_(record)

            # Modify the geometry if a node threshold is provided. This breaks the polygon object into pieces with the
            # approximate node count.
            if self.node_threshold is not None and get_node_count(record['geom']) > self.node_threshold:
                record['geom'] = get_split_polygon_by_node_threshold(record['geom'], self.node_threshold)

            if return_uid:
                uid = record['properties'][self.name_uid]
                yld = (uid, record)
            else:
                yld = record
            yield yld

    def _get_records_(self, select_uid=None, slice=slice):
        gi = GeomCabinetIterator(path=self.path, uid=self.name_uid, select_uid=select_uid, slice=slice)
        return gi

    def _validate_record_(self, record):
        geom = record['geom']

        # This should happen before any buffering. The buffering check may result in a single polygon object.
        if not self.allow_multipart and isinstance(geom, BaseMultipartGeometry):
            msg = 'Only singlepart geometries allowed. Perhaps "ugrid.convert_multipart_to_singlepart" would be useful?'
            raise ValueError(msg)


def get_split_array(arr, break_value):
    """
    :param arr: One-dimensional array.
    :type arr: :class:`numpy.ndarray`
    :type break_value: int
    :return_type: sequence of :class:`numpy.ndarray`
    """

    where = np.where(arr == break_value)
    split = np.array_split(arr, where[0])
    ret = [None] * len(split)
    ret[0] = split[0]
    for idx in range(1, len(ret)):
        ret[idx] = split[idx][1:]
    return ret


def get_oriented_and_valid_geometry(geom):
    try:
        assert geom.is_valid
    except AssertionError:
        geom = geom.buffer(0)
        assert geom.is_valid

    if not geom.exterior.is_ccw:
        geom = orient(geom)

    return geom


def convert_collection_to_esmf_format(fmobj, ds, polygon_break_value=None, start_index=0, face_uid_name=None):
    """
    Convert to an ESMF format NetCDF files. Only supports ragged arrays.

    :param fm: Flexible mesh object to convert.
    :type fm: :class:`pyugrid.flexible_mesh.core.FlexibleMesh`
    :param ds: An open netCDF4 dataset object.
    :type ds: :class:`netCDF4.Dataset`
    """
    # tdk: doc

    # face_areas = fmobj.face_areas
    # face_coordinates = fmobj.face_coordinates
    # if face_uid_name is None:
    #     face_uid_value = None
    # else:
    #     face_uid_value = fmobj.data[face_uid_name].data
    # faces = fmobj.faces
    # nodes = fmobj.nodes

    face_areas = fmobj['face_areas'].value
    face_coordinates = fmobj['face_coordinates'].value
    if face_uid_name is not None:
        face_uid_value = fmobj[face_uid_name].value
    else:
        face_uid_value = None
    faces = fmobj['face'].value
    nodes = fmobj['nodes'].value

    float_dtype = np.float32
    int_dtype = np.int32

    # Transform ragged array to one-dimensional array.
    num_element_conn_data = [e.shape[0] for e in faces.flat]
    length_connection_count = sum(num_element_conn_data)
    element_conn_data = np.zeros(length_connection_count, dtype=faces[0].dtype)
    start = 0
    for ii in faces.flat:
        element_conn_data[start: start + ii.shape[0]] = ii
        start += ii.shape[0]

    ####################################################################################################################

    from ocgis.new_interface.variable import Variable, VariableCollection
    coll = VariableCollection()

    coll.add_variable(Variable('nodeCoords', value=nodes, dtype=float_dtype,
                               dimensions=['nodeCount', 'coordDim'], units='degrees'))

    elementConn = Variable('elementConn', value=element_conn_data, dimensions='connectionCount',
                           attrs={'long_name': 'Node indices that define the element connectivity.',
                                  'start_index': start_index})
    if polygon_break_value is not None:
        elementConn.attrs['polygon_break_value'] = polygon_break_value
    coll.add_variable(elementConn)

    coll.add_variable(Variable('numElementConn', value=num_element_conn_data, dimensions='elementCount',
                               dtype=int_dtype, attrs={'long_name': 'Number of nodes per element.'}))

    coll.add_variable(Variable('centerCoords', value=face_coordinates, dimensions=['elementCount', 'coordDim'],
                               units='degrees', dtype=float_dtype))

    if face_uid_name is not None:
        coll.add_variable(Variable(face_uid_name, value=face_uid_value, dimensions='elementCount',
                                   attrs={'long_name': 'Element unique identifier.'}))

    coll.add_variable(Variable('elementArea', value=face_areas, dimensions='elementCount',
                               attrs={'units': 'degrees', 'long_name': 'Element area in native units.'},
                               dtype=float_dtype))

    coll.attrs['gridType'] = 'unstructured'
    coll.attrs['version'] = '0.9'
    coll.attrs['coordDim'] = 'longitude latitude'

    coll.write(ds)

    # # Dimensions #######################################################################################################
    #
    # node_count = ds.createDimension('nodeCount', nodes.shape[0])
    # element_count = ds.createDimension('elementCount', faces.shape[0])
    # coord_dim = ds.createDimension('coordDim', 2)
    # # element_conn_vltype = ds.createVLType(fm.faces[0].dtype, 'elementConnVLType')
    # connection_count = ds.createDimension('connectionCount', length_connection_count)
    #
    # # Variables ########################################################################################################
    #
    # node_coords = ds.createVariable('nodeCoords', nodes.dtype, (node_count.name, coord_dim.name))
    # node_coords.units = 'degrees'
    # node_coords[:] = nodes
    #
    # element_conn = ds.createVariable('elementConn', element_conn_data.dtype, (connection_count.name,))
    # element_conn.long_name = 'Node indices that define the element connectivity.'
    # if polygon_break_value is not None:
    #     element_conn.polygon_break_value = polygon_break_value
    # element_conn.start_index = start_index
    # element_conn[:] = element_conn_data
    #
    # num_element_conn = ds.createVariable('numElementConn', np.int32, (element_count.name,))
    # num_element_conn.long_name = 'Number of nodes per element.'
    # num_element_conn[:] = num_element_conn_data
    #
    # center_coords = ds.createVariable('centerCoords', face_coordinates.dtype, (element_count.name, coord_dim.name))
    # center_coords.units = 'degrees'
    # center_coords[:] = face_coordinates
    #
    # if face_uid_value is not None:
    #     uid = ds.createVariable(face_uid_name, face_uid_value.dtype, dimensions=(element_count.name,))
    #     uid[:] = face_uid_value
    #     uid.long_name = 'Element unique identifier.'
    #
    # element_area = ds.createVariable('elementArea', nodes.dtype, (element_count.name,))
    # element_area[:] = face_areas
    # element_area.units = 'degrees'
    # element_area.long_name = 'Element area in native units.'
    #
    # # tdk: element mask required?
    # # element_mask = ds.createVariable('elementMask', np.int32, (element_count.name,))
    #
    # # Global Attributes ################################################################################################
    #
    # ds.gridType = 'unstructured'
    # ds.version = '0.9'
    # setattr(ds, coord_dim.name, "longitude latitude")


def get_split_polygon_by_node_threshold(geom, node_threshold):
    # tdk: doc
    node_schema = get_node_schema(geom)

    # Collect geometries with node counts higher than the threshold.
    to_split = []
    for k, v in node_schema.items():
        if v['node_count'] > node_threshold:
            to_split.append(k)

    # Identify split parameters for an element exceeding the node threshold.
    for ii in to_split:
        n = node_schema[ii]
        # Approximate number of splits need for each split element to be less than the node threshold.
        n.n_splits = int(np.ceil(n['node_count'] / node_threshold))
        # This is the shape of the polygon grid to use for splitting the target element.
        n.split_shape = np.sqrt(n.n_splits)
        # There should be at least two splits.
        if n.split_shape == 1:
            n.split_shape += 1
        n.split_shape = tuple([int(np.ceil(ns)) for ns in [n.split_shape] * 2])

        # Get polygons to use for splitting.
        n.splitters = get_split_polygons(n['geom'], n.split_shape)

        # Create the individual splits:
        n.splits = []
        for s in n.splitters:
            if n.geom.intersects(s):
                the_intersection = n.geom.intersection(s)
                for ti in get_iter(the_intersection, dtype=Polygon):
                    n.splits.append(ti)

                    # write_fiona(n.splits, '01-splits')

    # Collect the polygons to return as a multipolygon.
    the_multi = []
    for v in node_schema.values():
        if 'splits' in v:
            the_multi += v.splits
        else:
            the_multi.append(v.geom)

    return MultiPolygon(the_multi)


def get_node_schema(geom):
    # tdk: doc
    ret = Dict()
    for ctr, ii in enumerate(get_iter(geom, dtype=Polygon)):
        ret[ctr].node_count = get_node_count(ii)
        ret[ctr].area = ii.area
        ret[ctr].geom = ii
    return ret


def get_node_count(geom):
    node_count = 0
    for ii in get_iter(geom, dtype=Polygon):
        node_count += len(ii.exterior.coords)
    return node_count


def get_split_polygons(geom, split_shape):
    from ocgis.new_interface.variable import Variable
    from ocgis.new_interface.grid import GridXY

    minx, miny, maxx, maxy = geom.bounds
    rows = np.linspace(miny, maxy, split_shape[0])
    cols = np.linspace(minx, maxx, split_shape[1])

    row = Variable(value=rows, name='row', dimensions='row')
    col = Variable(value=cols, name='col', dimensions='col')
    grid = GridXY(col, row)
    grid.set_extrapolated_bounds('x', 'y', 'corners')
    return grid.polygon.value.flatten().tolist()


def get_iter(element, dtype=None):
    """
    :param element: The element comprising the base iterator. If the element is a ``basestring`` or :class:`numpy.ndarray`
     then the iterator will return the element and stop iteration.
    :type element: varying
    :param dtype: If not ``None``, use this argument as the argument to ``isinstance``. If ``element`` is an instance of
     ``dtype``, ``element`` will be placed in a list and passed to ``iter``.
    :type dtype: type or tuple
    """

    if dtype is not None:
        if isinstance(element, dtype):
            element = (element,)

    if isinstance(element, (basestring, np.ndarray)):
        it = iter([element])
    else:
        try:
            it = iter(element)
        except TypeError:
            it = iter([element])

    return it
