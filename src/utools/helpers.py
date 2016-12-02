import os
from contextlib import contextmanager
from datetime import datetime

import fiona
import netCDF4 as nc
from fiona.crs import from_epsg
from shapely.geometry import mapping


def get_datetime_fp_string():
    now = datetime.now()
    return now.strftime('%Y%m%d-%H%M%S')


def format_bool(value):
    """
    Format a string to boolean.

    :param value: The value to convert.
    :type value: int or str
    """

    try:
        ret = bool(int(value))
    except ValueError:
        value = value.lower()
        if value in ['t', 'true']:
            ret = True
        elif value in ['f', 'false']:
            ret = False
        else:
            raise ValueError('String not recognized for boolean conversion: {0}'.format(value))
    return ret


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

    if isinstance(element, basestring):
        it = iter([element])
    else:
        try:
            it = iter(element)
        except TypeError:
            it = iter([element])

    return it


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
