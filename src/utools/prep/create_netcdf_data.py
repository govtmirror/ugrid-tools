import netCDF4 as nc
import numpy as np

from utools.io.helpers import get_bounds_from_1d, get_exact_field


def create_high_resolution_ucar_grid():
    path = '/tmp/high_resolution_uccar_exact_data_20160811.nc'
    lon = np.linspace(-133.50735, -60.492672, num=4608)
    lat = np.linspace(20.077797, 57.772186, num=3840)
    ttime = [10.]
    create_source_netcdf_data(path, lon, lat, ttime)


def create_source_netcdf_data(path, lon, lat, ttime, variable_name='exact'):
    ds = nc.Dataset(path, 'w', format='NETCDF3_CLASSIC')
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

        mlon, mlat = np.meshgrid(lon, lat)
        exact = get_exact_field(mlat, mlon)
        fill_exact = np.zeros((len(ttime), lat.shape[0], lon.shape[0]), dtype=np.float32)
        fill_exact[:] = exact
        vexact = ds.createVariable(variable_name, np.float32, dimensions=('time', 'lat', 'lon'))
        vexact[:] = fill_exact
    finally:
        ds.close()


if __name__ == '__main__':
    create_high_resolution_ucar_grid()
