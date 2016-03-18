import netCDF4 as nc
import os
import tempfile
import ESMF
import datetime
from fiona.crs import from_epsg
import ugrid
import logging
import ocgis
from ugrid.convert import mesh2_nc_to_fiona
from ugrid.core import GeometryManager
from ugrid.helpers import create_rtree_file
from mpi4py import MPI
import sys
import numpy as np
from ocgis.interface.base.dimension.base import VectorDimension
from dispatch import MPI_COMM_WORLD

log = logging.getLogger('pmesh')
log.parent = None
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter(fmt='[%(asctime)s] %(levelname)s: %(name)s: %(message)s',
                                       datefmt='%Y-%m-%d %H:%M:%S'))
log.addHandler(console)


PATH_CATCHMENT_SHP = '/home/benkoziol/Dropbox/NESII/project/pmesh/bin/NHDPlusTX/NHDPlus12/NHDPlusCatchment/Catchment.shp'
# DIR_OUTPUT = tempfile.mkdtemp()
PATH_CLIMATE_DATA = '/home/benkoziol/htmp/pmesh/nldas_met_update.obs.daily.pr.1990.nc'
# PATH_CLIMATE_DATA = '/home/benkoziol/data/climate_data/CanCM4/tas_day_CanCM4_decadal2000_r2i1p1_20010101-20101231.nc'
# PATH_CLIMATE_DATA = '/home/benkoziol/data/climate_data/QED-2013/sfwe/maurer02v2/pr/pr.nc'
DIR_OUTPUT = os.path.expanduser('~/htmp/pmesh')
FILENAME_CATCHMENT_UGRID = 'catchments.nc'
FILENAME_CATCHMENT_SINGLEPART_SHAPEFILE = 'catchment_singlepart_with_uid2.shp'
FILENAME_RTREE = 'rtree.catchments'
FILENAME_UGRID_SHAPEFILE = 'from_ugrid.shp'

PATH_SINGLEPART_SHAPEFILE = os.path.join(DIR_OUTPUT, FILENAME_CATCHMENT_SINGLEPART_SHAPEFILE)
PATH_RTREE = os.path.join(DIR_OUTPUT, FILENAME_RTREE)
PATH_UGRID_FILE = os.path.join(DIR_OUTPUT, FILENAME_CATCHMENT_UGRID)
PATH_UGRID_SHAPEFILE = os.path.join(DIR_OUTPUT, FILENAME_UGRID_SHAPEFILE)
PATH_FAKE_DATA = os.path.join(DIR_OUTPUT, 'fake_data.nc')
MPI_RANK = MPI.COMM_WORLD.Get_rank()


def convert_shapefile_to_ugrid():
    # log.info('creating spatial index')
    # gm = GeometryManager('GID', path=PATH_SINGLEPART_SHAPEFILE)
    # create_rtree_file(gm, PATH_RTREE)

    if MPI_RANK == 0:
        log.info('creating netcdf file')
    ugrid.fiona_to_mesh2_nc(PATH_SINGLEPART_SHAPEFILE, 'GID', PATH_UGRID_FILE, rtree_path=PATH_RTREE,
                            nc_format='NETCDF3_CLASSIC')

    if MPI_RANK == 0:
        log.info('success')
    else:
        log.info('finished (rank={0})'.format(MPI_RANK))


def regrid():

    ESMF.Manager(debug=True)

    log.info('getting source field')

    grid = ESMF.Grid(filename=PATH_FAKE_DATA, filetype=ESMF.FileFormat.GRIDSPEC)
    srcfield = ESMF.Field(grid, staggerloc=ESMF.StaggerLoc.CENTER)#, ndbounds=[2])
    srcfield.read(filename=PATH_FAKE_DATA, variable="pr")

    # create an ESMPy Mesh and destination Field from UGRID file
    log.info('getting destination mesh')
    dstgrid = ESMF.Mesh(filename=PATH_UGRID_FILE, filetype=ESMF.FileFormat.UGRID, meshname="Mesh2")
    log.info('getting destination field')
    dstfield = ESMF.Field(dstgrid, "dstfield", meshloc=ESMF.MeshLoc.ELEMENT, ndbounds=[366])

    # create an object to regrid data from the source to the destination field
    log.info('creating regrid object')
    regrid = ESMF.Regrid(srcfield, dstfield, regrid_method=ESMF.RegridMethod.CONSERVE,
                         unmapped_action=ESMF.UnmappedAction.IGNORE)

    # do the regridding from source to destination field
    log.info('executing regrid')
    dstfield = regrid(srcfield, dstfield)

    import ipdb;ipdb.set_trace()


def create_data():
    col = np.linspace(-104., -100., 100)
    row = np.linspace(32, 36, 100)

    col = VectorDimension(value=col, name='longitude', name_bounds='longitude_bounds', attrs={'standard_name': 'longitude',
                                                                                              'units': 'degrees_east'})
    col.set_extrapolated_bounds()
    row = VectorDimension(value=row, name='latitude', name_bounds='latitude_bounds', attrs={'standard_name': 'latitude',
                                                                                            'units': 'degrees_north'})
    row.set_extrapolated_bounds()
    grid = ocgis.SpatialGridDimension(row=row, col=col)
    sdim = ocgis.SpatialDimension(grid=grid)

    start = datetime.datetime(2000, 1, 1)
    stop = datetime.datetime(2000, 12, 31)
    days = 1
    ret = []
    delta = datetime.timedelta(days=days)
    check = start
    while check <= stop:
        ret.append(check)
        check += delta
    temporal = ocgis.TemporalDimension(value=ret, unlimited=True)

    var_value = np.ones((1, temporal.shape[0], 1, row.shape[0], col.shape[0]), dtype=float)
    variable = ocgis.Variable(value=var_value, name='pr')

    field = ocgis.Field(spatial=sdim, temporal=temporal, variables=variable)

    ds = nc.Dataset(PATH_FAKE_DATA, 'w', format='NETCDF3_CLASSIC')
    field.write_netcdf(ds)
    ds.close()


def prepare_shapefile():
    ugrid.convert_multipart_to_singlepart(PATH_CATCHMENT_SHP, PATH_SINGLEPART_SHAPEFILE, new_uid_name='UGID')


def add_unique_identifier():
    in_path = os.path.expanduser('~/htmp/pmesh/catchment_singlepart_with_uid.shp')
    out_path = os.path.expanduser('~/htmp/pmesh/catchment_singlepart_with_uid2.shp')
    ocgis.util.helpers.add_shapefile_unique_identifier(in_path, out_path, name='GID')


def convert_ugrid_to_shapefile():
    mesh2_nc_to_fiona(PATH_UGRID_FILE, PATH_UGRID_SHAPEFILE, crs=from_epsg(4326))


if __name__ == '__main__':
    # add_unique_identifier()
    # prepare_shapefile()
    convert_shapefile_to_ugrid()
    # convert_ugrid_to_shapefile()
    # create_data()
    # regrid()
