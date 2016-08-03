import os
from contextlib import contextmanager

import fiona
import netCDF4 as nc
from fiona.crs import from_epsg
from shapely.geometry import mapping


@contextmanager
def nc_scope(path, mode='r', format=None):
    """
    Provide a transactional scope around a :class:`netCDF4.Dataset` object.

    >>> with nc_scope('/my/file.nc') as ds:
    >>>     print ds.variables

    :param str path: The full path to the netCDF dataset.
    :param str mode: The file mode to use when opening the dataset.
    :param str format: The NetCDF format.
    :returns: An open dataset object that will be closed after leaving the ``with`` statement.
    :rtype: :class:`netCDF4.Dataset`
    """

    kwds = {'mode': mode}
    if format is not None:
        kwds['format'] = format

    ds = nc.Dataset(path, **kwds)
    try:
        yield ds
    finally:
        ds.close()


def write_fiona(target, filename_no_suffix, folder='~/htmp', crs=None):
    """
    Write a geometry object or sequence of geometry to a shapefile.

    :param target: The geometry object to write.
    :param filename_no_suffix: The filename without the extension.
    :param folder: Directory to write to.
    :param crs: The coordinate system of the geometry objects.
    """

    schema = {'geometry': 'MultiPolygon', 'properties': {}}
    with fiona.open(os.path.expanduser(os.path.join(folder, '{}.shp'.format(filename_no_suffix))), mode='w',
                    schema=schema,
                    crs=from_epsg(4326), driver='ESRI Shapefile') as sink:
        for geom in target:
            feature = {'properties': {}, 'geometry': mapping(geom)}
            sink.write(feature)
