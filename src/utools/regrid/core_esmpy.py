from contextlib import contextmanager

import ESMF
import netCDF4 as nc
import numpy as np


def get_dstfield(path_ugrid_file, path_source_data, log, debug=False):
    ESMF.Manager(debug=debug)

    log.debug('getting source grid')
    srcgrid = get_esmf_grid_src(path_source_data)
    log.debug('getting source field')
    srcfield = get_field_src(srcgrid, path_source_data, 'pr')
    log.debug('srcfield shape: {0}'.format(srcfield.data.shape))

    log.debug('getting destination grid')
    dstgrid = ESMF.Mesh(filename=path_ugrid_file, filetype=ESMF.FileFormat.UGRID, meshname='mesh')
    # dstgrid = get_esmf_grid_src(path_source_data)

    log.debug('dstgrid (mesh) size: {}'.format(dstgrid.size))
    log.debug('getting destination field')

    dstfield = ESMF.Field(dstgrid, "dstfield", meshloc=ESMF.MeshLoc.ELEMENT, ndbounds=[366])
    # dstfield = ESMF.Field(dstgrid, "dstfield", ndbounds=[366])

    log.debug('creating regrid object')
    regrid = ESMF.Regrid(srcfield, dstfield, regrid_method=ESMF.RegridMethod.CONSERVE,
                         unmapped_action=ESMF.UnmappedAction.ERROR)
    # regrid = ESMF.Regrid(srcfield, dstfield, regrid_method=ESMF.RegridMethod.BILINEAR,
    #                      unmapped_action=ESMF.UnmappedAction.ERROR)

    log.debug('executing regrid')
    # "zero_region" only weighted data will be touched.
    dstfield = regrid(srcfield, dstfield, zero_region=ESMF.Region.SELECT)
    # dstfield = regrid(srcfield, dstfield)

    srcgrid.destroy()
    srcfield.destroy()
    regrid.destroy()

    return dstfield


def get_esmf_grid_src(filename):
    """Get the source ESMF grid object."""

    return ESMF.Grid(filename=filename, filetype=ESMF.FileFormat.GRIDSPEC, coord_names=['longitude', 'latitude'],
                     add_corner_stagger=True, is_sphere=False)


def get_field_src(grid, filename, variable):
    srcfield = ESMF.Field(grid, staggerloc=ESMF.StaggerLoc.CENTER, ndbounds=[366])
    start_col, start_row = grid.lower_bounds[0]
    stop_col, stop_row = grid.upper_bounds[0]
    with nc_scope(filename, 'r') as ds:
        var = ds.variables[variable]
        fill = var[:, start_row:stop_row, start_col:stop_col]
        fill = np.swapaxes(fill, 1, 2)
        srcfield.data[:] = fill
    return srcfield


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
