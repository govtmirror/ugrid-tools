import itertools

import netCDF4 as nc
import numpy as np

from utools.helpers import get_datetime_fp_string
from utools.io.helpers import get_bounds_from_1d, get_exact_field


def create_high_resolution_ucar_grid():
    path = '/tmp/high_resolution_ucar_exact_data_250m_{}.nc'.format(get_datetime_fp_string())
    lon = np.linspace(-133.50735, -60.492672, num=4608 * 4)
    lat = np.linspace(20.077797, 57.772186, num=3840 * 4)
    ttime = [10.]
    create_source_netcdf_data(path, lon, lat, ttime)


def create_source_netcdf_data(path, lon, lat, ttime, variable_name='exact'):
    ds = nc.Dataset(path, 'w')
    # ds = nc.Dataset(path, 'w', format='NETCDF3_CLASSIC')
    try:
        ds.createDimension('lon', size=len(lon))
        ds.createDimension('lat', size=len(lat))
        ds.createDimension('time', size=len(ttime))
        ds.createDimension('bnds', size=2)

        lon_bounds = get_bounds_from_1d(lon)
        lat_bounds = get_bounds_from_1d(lat)

        vlon = ds.createVariable('longitude', np.float32, dimensions=('lon',))
        vlon[:] = lon
        vlon.axis = 'X'
        vlon.bounds = 'longitude_bounds'
        vlon.standard_name = 'longitude'
        vlon.units = 'degrees_east'

        vlon_bounds = ds.createVariable('longitude_bounds', np.float32, dimensions=('lon', 'bnds'))
        vlon_bounds[:] = lon_bounds

        vlat = ds.createVariable('latitude', np.float32, dimensions=('lat',))
        vlat[:] = lat
        vlat.axis = 'Y'
        vlat.bounds = 'latitude_bounds'
        vlat.standard_name = 'latitude'
        vlat.units = 'degrees_north'

        vlat_bounds = ds.createVariable('latitude_bounds', np.float32, dimensions=('lat', 'bnds'))
        vlat_bounds[:] = lat_bounds

        vtime = ds.createVariable('time', np.float32, dimensions=('time',))
        vtime[:] = ttime
        vtime.axis = 'T'
        vtime.units = 'days since 2000-1-1'
        vtime.calendar = 'standard'

        # mlon, mlat = np.meshgrid(lon, lat)
        # exact = get_exact_field(mlat, mlon)
        exact_shape = (len(ttime), lat.shape[0], lon.shape[0])
        # fill_exact = np.zeros(exact_shape, dtype=np.float32)
        vexact = ds.createVariable(variable_name, np.float32, dimensions=('time', 'lat', 'lon'))
        for tidx, lat_idx, lon_idx in itertools.product(*[range(ii) for ii in exact_shape]):
            exact = get_exact_field(np.atleast_1d(lon[lon_idx]), np.atleast_1d(lat[lat_idx]))
            vexact[tidx, lat_idx, lon_idx] = exact[0]
            # vexact[:] = fill_exact
    finally:
        ds.close()


if __name__ == '__main__':
    create_high_resolution_ucar_grid()
