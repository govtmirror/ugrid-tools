import datetime

import netCDF4 as nc
import numpy as np
import ocgis

from pmesh.logging import log


def create_source_netcdf_data(path, row=None, col=None, analytic=False):
    field = get_ocgis_field(col, row, analytic=analytic)

    ds = nc.Dataset(path, 'w', format='NETCDF3_CLASSIC')
    field.write_netcdf(ds)
    ds.variables['time'].units = 'days since 2000-1-1'
    ds.variables['time'].calendar = 'standard'
    ds.close()


def get_ocgis_field(col=None, row=None, analytic=False):
    from ocgis import VectorDimension
    import ocgis

    if col is None:
        col = np.linspace(-126., -66., 240)
    if row is None:
        row = np.linspace(23., 53., 108)
    col = VectorDimension(value=col, name='longitude', name_bounds='longitude_bounds',
                          attrs={'standard_name': 'longitude',
                                 'units': 'degrees_east'})
    col.set_extrapolated_bounds()
    row = VectorDimension(value=row, name='latitude', name_bounds='latitude_bounds',
                          attrs={'standard_name': 'latitude',
                                 'units': 'degrees_north'})
    row.set_extrapolated_bounds()
    grid = ocgis.SpatialGridDimension(row=row, col=col)
    sdim = ocgis.SpatialDimension(grid=grid)
    start = datetime.datetime(2000, 1, 1)
    stop = datetime.datetime(2000, 1, 3)
    days = 1
    ret = []
    delta = datetime.timedelta(days=days)
    check = start
    while check <= stop:
        ret.append(check)
        check += delta
    temporal = ocgis.TemporalDimension(value=ret, unlimited=True)

    var_value = np.ones((1, temporal.shape[0], 1, row.shape[0], col.shape[0]), dtype=float)
    if analytic:
        # f(lat,lon) = 2+cos^2(lat) + cos(2lon)
        radians = grid.value.copy()
        radians[1] += 360.
        radians *= 0.0174533
        # radians = radians * 0.0174533
        fill = 2 + np.cos(radians[0])**2 + np.cos(2 * radians[1])
        # fill = grid.value[0, :, :] * (grid.value[1, :, :] + 360.)**2
        var_value[:] = fill
    else:
        for idx in range(var_value.shape[1]):
            var_value[:, idx, :, :, :] = var_value[:, idx, :, :, :] * idx

    variable = ocgis.Variable(value=var_value, name='pr')
    field = ocgis.Field(spatial=sdim, temporal=temporal, variables=variable)
    return field


if __name__ == '__main__':
    ocgis.env.DIR_OUTPUT = '/tmp'
    ocgis.env.OVERWRITE = True

    path = '/tmp/analytic-conus_20160316-1737.nc'
    create_source_netcdf_data(path, analytic=True)
    ops = ocgis.OcgOperations(dataset={'uri': path}, snippet=True, output_format='shp', prefix='analytic-conus')

    # Create analytical data for Texas catchments.
    # row = np.arange(32.0012, 32.4288 + 0.02, 0.01)
    # col = np.arange(-95.0477, -94.7965 + 0.02, 0.01)
    # path = '/tmp/analytic_20160316-1627.nc'
    # create_source_netcdf_data(path, row=row, col=col, analytic=True)
    # ops = ocgis.OcgOperations(dataset={'uri': path}, snippet=True, output_format='shp', prefix='analytic')

    log.info(ops.execute())
