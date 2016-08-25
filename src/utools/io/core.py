from utools.constants import UgridToolsConstants
from utools.logging import log


def from_geometry_manager(gm, mesh_name='mesh', use_ragged_arrays=False, with_connectivity=True):
    return get_flexible_mesh(gm, mesh_name, use_ragged_arrays, with_connectivity=with_connectivity)


def from_shapefile(path, name_uid, mesh_name='mesh', path_rtree=None, use_ragged_arrays=False, with_connectivity=True,
                   allow_multipart=False, node_threshold=None, driver_kwargs=None, debug=False, dest_crs=None):
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
    from utools.io.geom_manager import GeometryManager

    if debug:
        slc = [0, 1]
    else:
        slc = None

    log.debug('creating geometry manager')
    log.debug(('driver_kwargs', driver_kwargs))
    gm = GeometryManager(name_uid, path=path, path_rtree=path_rtree, allow_multipart=allow_multipart,
                         node_threshold=node_threshold, slc=slc, driver_kwargs=driver_kwargs, dest_crs=dest_crs)
    log.debug('geometry manager created')

    ret = get_flexible_mesh(gm, mesh_name, use_ragged_arrays, with_connectivity=with_connectivity)
    log.debug('mesh collection returned')

    return ret


def get_flexible_mesh(gm, mesh_name, use_ragged_arrays, with_connectivity=True):
    from helpers import get_variables

    result = get_variables(gm, use_ragged_arrays=use_ragged_arrays, with_connectivity=with_connectivity)

    ret = {}
    face_nodes, face_edges, edge_nodes, nodes, face_links, face_ids, face_coordinates, face_areas, section = result
    ret['face'] = face_nodes
    ret['face_edges'] = face_edges
    ret['edge_nodes'] = edge_nodes
    ret['nodes'] = nodes
    ret['face_coordinates'] = face_coordinates
    ret['face_areas'] = face_areas
    ret['section'] = section
    ret[gm.name_uid] = face_ids
    if face_links is not None:
        ret['face_links'] = face_links

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
