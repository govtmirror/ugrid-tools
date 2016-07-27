from mpi import MPI_RANK
from utools.constants import UgridToolsConstants


def from_geometry_manager(gm, mesh_name='mesh', use_ragged_arrays=False, with_connectivity=True):
    return get_flexible_mesh(gm, mesh_name, use_ragged_arrays, with_connectivity=with_connectivity)


def from_shapefile(path, name_uid, mesh_name='mesh', path_rtree=None, use_ragged_arrays=False, with_connectivity=True,
                   allow_multipart=False, node_threshold=None):
    """
    Create a flexible mesh from a target shapefile.

    >>> path = '/input/target.shp'
    >>> name_uid = 'UID'
    >>> fm = FlexibleMesh.from_shapefile(path, name_uid)

    :param path: Path to the target shapefile.
    :type path: str
    :param name_uid: Name of the integer unique identifier in the target shapefile. This value will be maintained on
     the output mesh object.
    :type name_uid: str
    :param mesh_name: Name of the mesh catalog variable.
    :type mesh: str
    :param path_rtree: Path to a serialized spatial index object created using ``rtree``. Use :func:`pyugrid.flexible_mesh.helpers.create_rtree_file`
     to create a persistent ``rtree`` spatial index file.
    :type path_rtree: str
    :rtype: :class:`pyugrid.flexible_mesh.core.FlexibleMesh`
    """
    # tdk: update doc
    from helpers import GeometryManager

    gm = GeometryManager(name_uid, path=path, path_rtree=path_rtree, allow_multipart=allow_multipart,
                         node_threshold=node_threshold)
    ret = get_flexible_mesh(gm, mesh_name, use_ragged_arrays, with_connectivity=with_connectivity)

    return ret


def get_flexible_mesh(gm, mesh_name, use_ragged_arrays, with_connectivity=True):
    from helpers import get_variables
    from ocgis.new_interface.variable import Variable, VariableCollection

    result = get_variables(gm, use_ragged_arrays=use_ragged_arrays, with_connectivity=with_connectivity)
    if MPI_RANK == 0:
        coll = VariableCollection()

        face_nodes, face_edges, edge_nodes, nodes, face_links, face_ids, face_coordinates, face_areas = result
        face_nodes = Variable('face', value=face_nodes, dimensions='element_count')
        face_edges = Variable('face_edges', value=face_edges, dimensions='element_count')
        edge_nodes = Variable('edge_nodes', value=edge_nodes, dimensions=['node_count', 'coord_dim'])
        nodes = Variable('nodes', value=nodes, dimensions=['node_count', 'coord_dim'])
        if face_links is not None:
            face_links = Variable('face_links', value=face_links, dimensions=['element_count'])
        face_coordinates = Variable('face_coordinates', value=face_coordinates,
                                    dimensions=['element_count', 'coord_dim'])
        face_areas = Variable('face_areas', value=face_areas, dimensions=['element_count'])
        face_uid = Variable(gm.name_uid, value=face_ids, dimensions='element_count')

        coll.add_variable(face_nodes)
        coll.add_variable(face_edges)
        coll.add_variable(edge_nodes)
        coll.add_variable(nodes)
        coll.add_variable(face_coordinates)
        coll.add_variable(face_areas)
        if face_links is not None:
            coll.add_variable(face_links)
        coll.add_variable(face_uid)

        # data_attrs = {'long_name': 'Face unique identifiers.'}
        # data = {'': UVar(gm.name_uid, location='face', data=face_ids, attributes=data_attrs)}
        # ret = FlexibleMesh(nodes=nodes, faces=face_nodes, edges=edge_nodes, boundaries=None,
        #                    face_face_connectivity=face_links, face_edge_connectivity=face_edges,
        #                    edge_coordinates=None, face_coordinates=face_coordinates, boundary_coordinates=None,
        #                    data=data, mesh_name=mesh_name, face_areas=face_areas)

        ret = coll
    else:
        ret = None
    return ret


def iter_records(coll, data_variables=None, shapely_only=False):
    """
    Yield record dictionaries containing face coordinates and properties (i.e. data set names and values).

    >>> fm = FlexibleMesh(...)
    >>> for record in fm.iter_records():
    >>>     print(record)
    >>> {'geometry': 'type': 'Polygon', 'coordinates': (...,), properties: {'a': 5, ...}}

    :param shapely_only: If ``True``, yield Shapely geometries instead of GeoJSON mappings for the face coordinates.
     In place of a ``'geometry'`` key, there is a ``'geom'`` key mapped to a Shapely geometry object.
    :type shapely_only: bool
    :rtype: dict
    """

    from helpers import iter_records

    faces = coll['faces'].value
    nodes = coll['nodes'].value

    if data_variables is not None:
        data_variables = [coll[d] for d in data_variables]
    else:
        data_variables = None

    for record in iter_records(faces, nodes[:, 0], nodes[:, 1], datasets=data_variables,
                               shapely_only=shapely_only,
                               polygon_break_value=UgridToolsConstants.POLYGON_BREAK_VALUE):
        yield record


def save_as_shapefile(coll, path, face_uid_name=None):
    """
    Save object as a shapefile.

    >>> path = '/out_location/my.shp'
    >>> fm = FlexibleMesh(...)
    >>> fm.save_as_shapefile(path, face_uid_name='UID_VAR')

    :param path: Path to the output shapefile.
    :type path: str
    :param face_uid_name: Name of the unique, integer identifier variable contained in :attr:`pyugrid.ugrid.UGrid.data`.
    :type face_uid_name: str
    """

    from helpers import flexible_mesh_to_fiona

    if face_uid_name is not None:
        face_uid = coll[face_uid_name].value
    else:
        face_uid = None

    faces = coll['faces'].value
    nodes = coll['nodes'].value

    flexible_mesh_to_fiona(path, faces, nodes[:, 0], nodes[:, 1], face_uid=face_uid)
