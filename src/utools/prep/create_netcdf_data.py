import itertools

import netCDF4 as nc
import numpy as np

from utools.helpers import get_datetime_fp_string
from utools.io.helpers import get_bounds_from_1d, get_exact_field


def create_high_resolution_ucar_grid():
    path = '/tmp/high_resolution_ucar_exact_data_500m_{}.nc'.format(get_datetime_fp_string())
    lon = np.linspace(-133.50735, -60.492672, num=4608 * 2)
    lat = np.linspace(20.077797, 57.772186, num=3840 * 2)
    ttime = [10.]
    create_source_netcdf_data(path, lon, lat, ttime, create_data_variable=False)


def create_source_netcdf_data(path, lon, lat, ttime, variable_name='exact', create_data_variable=True):
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

        if create_data_variable:
            mlon, mlat = np.meshgrid(lon, lat)
            exact_shape = (len(ttime), lat.shape[0], lon.shape[0])
            vexact = ds.createVariable(variable_name, np.float32, dimensions=('time', 'lat', 'lon'))
            # Use this fill fill approach to avoid memory issues with large grids.
            for tidx, lon_idx in itertools.product(*[range(ii) for ii in [exact_shape[0], exact_shape[1]]]):
                exact = get_exact_field(mlon[:, lon_idx], mlat[:, lon_idx])
                vexact[tidx, :, lon_idx] = exact
    finally:
        ds.close()


if __name__ == '__main__':
    create_high_resolution_ucar_grid()
