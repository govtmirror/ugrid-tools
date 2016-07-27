import itertools
import os
from functools import partial

import ESMF
import fiona
import numpy as np
import ocgis
from mpi4py import MPI
from ocgis.util.geom_cabinet import GeomCabinetIterator
from pyugrid import FlexibleMesh
from shapely.geometry import Point, mapping

from utools.regrid.core_esmpy import get_dstfield, get_esmf_grid_src, get_field_src
from utools.test.base import AbstractUToolsTest

COMM = MPI.COMM_WORLD
RANK = COMM.Get_rank()

PATH_CATCHMENTS_SUBSET = '/home/benkoziol/htmp/pmesh/catchment_singlepart_with_uid2.shp'
# PATH_UGRID_NC = '/home/benkoziol/htmp/pmesh/output/catchment_ugrid.nc'
PATH_UGRID_NC = '/home/ubuntu/pmesh/bin/catchment_ugrid.nc'
# PATH_UGRID_NC = '/home/benkoziol/htmp/pmesh/new_ugrid_with_polygon_break_value.nc'
# PATH_SYNTHETIC_SOURCE_DATA = '/home/benkoziol/htmp/pmesh/output/precipitation_synthetic.nc'
PATH_SYNTHETIC_SOURCE_DATA = '/home/ubuntu/pmesh/bin/precipitation_synthetic.nc'
PATH_OUTPUT = '/home/benkoziol/htmp/pmesh/output'
MESH_NAME = 'mesh'
NAME_UID = 'UGID'
NETCDF_FORMAT = 'NETCDF3_CLASSIC'


class Test(AbstractUToolsTest):

    def create_ugrid_netcdf(self, in_shp=PATH_CATCHMENTS_SUBSET, out_nc=PATH_UGRID_NC, name_uid=NAME_UID):
        """Create a UGRID netcdf file from an input singlepart shapefile."""

        fm = FlexibleMesh.from_shapefile(in_shp, name_uid)
        fm.save_as_netcdf(out_nc, kwargs_dataset={'format': NETCDF_FORMAT})

    def create_elements_shapefile(self, in_shp, out_shp, predicate):
        """Create shapefile containing elements selected by the predicate function."""

        with fiona.open(in_shp) as source:
            with fiona.open(out_shp, mode='w', **source.meta) as sink:
                for record in source:
                    if predicate(record):
                        sink.write(record)

    def create_grid_shp_from_nc(self, in_nc, prefix='nc_shp'):
        """Create a shapefile from a gridded netCDF file."""

        dir_output = PATH_OUTPUT
        ops = ocgis.OcgOperations(dataset={'uri': in_nc}, output_format='shp', snippet=True, dir_output=dir_output,
                                  prefix=prefix)
        return ops.execute()

    def test_domain_overlap(self):
        """Test all points from the source UGRID coordinates are found in the source data coverage."""

        path_source = PATH_SYNTHETIC_SOURCE_DATA
        path_source = '/home/benkoziol/Dropbox/Share/Transfer/pmesh/single-element-failure-20151204/precipitation_synthetic.nc'
        rd = ocgis.RequestDataset(uri=path_source)
        ops = ocgis.OcgOperations(dataset=rd, output_format='shp', dir_output='/tmp', prefix='precipitation_synthetic',
                                  snippet=True)
        ops.execute()
        field = rd.get()
        # polygons = field.spatial.geom.polygon.value
        extent_polygon = field.spatial.grid.extent_polygon

        ugrid_path = PATH_UGRID_NC
        ugrid_path = '/home/benkoziol/Dropbox/Share/Transfer/pmesh/single-element-failure-20151204/catchment_ugrid.nc'
        with self.nc_scope(ugrid_path) as ds:
            lat = ds.variables['mesh_node_lat'][:]
            lon = ds.variables['mesh_node_lon'][:]

        out_pt = '/tmp/out_points.shp'
        schema = {'geometry': 'Point', 'properties': {}}

        with fiona.open(out_pt, 'w', schema=schema, driver='ESRI Shapefile') as sink:

            for idx in range(lat.shape[0]):
                print '{} of {}'.format(idx + 1, lat.shape[0])
                pt = Point(lon[idx], lat[idx])
                # print pt
                record = {'geometry': mapping(pt), 'properties': {}}
                sink.write(record)
                self.assertTrue(extent_polygon.contains(pt))

    def test_2d_flexible_mesh(self):
        self.set_debug(True)

        ESMF.Manager(debug=True)

        in_shp = os.path.join(self.path_bin, '2d_flexible_mesh', '2d_flexible_mesh.shp')
        ugrid_nc_path = self.get_temporary_file_path('out_ugrid.nc')
        source_nc_path = self.get_temporary_file_path('source_data.nc')

        self.create_ugrid_netcdf(in_shp, ugrid_nc_path, name_uid='id')

        row = np.linspace(-1.077, 1.247, num=4)
        col = np.linspace(-1.939, 1.882, num=4)
        self.create_source_netcdf_data(source_nc_path, row=row, col=col)
        field = self.get_ocgis_field(row=row, col=col)
        grid_esmf = get_esmf_grid_from_sdim(field.spatial)

        self.log.debug(self.create_grid_shp_from_nc(source_nc_path, prefix='prcp_data'))

        dstfield = self.get_dstfield(source_nc_path, ugrid_nc_path, grid_esmf=grid_esmf)
        self.assertAlmostEqual(np.mean(dstfield), 1.0)

    def test_create_source_netcdf_data(self):
        self.create_source_netcdf_data(PATH_SYNTHETIC_SOURCE_DATA)
        self.create_grid_shp_from_nc(PATH_SYNTHETIC_SOURCE_DATA, prefix='precipitation_synthetic')

    def test_create_ugrid_netcdf(self):
        self.create_ugrid_netcdf()

    def test_get_field_src(self):
        ESMF.Manager(debug=True)
        self.set_debug(True)

        if RANK == 0:
            filename = self.get_temporary_file_path('out.nc')
            self.create_source_netcdf_data(filename)
            self.nc_dump(filename)
        else:
            filename = None

        filename = COMM.bcast(filename, root=0)
        self.log.debug((RANK, filename))

        grid = get_esmf_grid_src(filename)
        self.assertIsInstance(grid, ESMF.Grid)

        field = get_field_src(grid, filename, 'pr')
        self.assertIsInstance(field, ESMF.Field)

        self.log.debug((RANK, field.data.shape))

    def test_subset_regridding(self):
        """Test regridding a small subset of the Texas regions. 281 elements are included in this test."""
        # tdk: test regridding the whole domain is failing
        # Data available at: https://www.dropbox.com/s/dmsexup1kshfav0/data-mesh_failure.zip?dl=0
        self.set_debug(True)

        field_esmf = get_dstfield(PATH_UGRID_NC, PATH_SYNTHETIC_SOURCE_DATA, self.log, debug=True)

    def test_subset_regridding_by_element(self):
        """Test regridding a subset of Texas element by element."""
        self.set_debug(True)

        def _pred_(record, ugid=None):
            if record['properties'][NAME_UID] in ugid:
                ret = True
            else:
                ret = False
            return ret

        single_element_shapefile = self.get_temporary_file_path('catchment.shp')
        out_ugrid_nc = self.get_temporary_file_path('catchment_ugrid.nc')

        for r in GeomCabinetIterator(path=PATH_CATCHMENTS_SUBSET):
            ugid = r['properties'][NAME_UID]

            # if ugid != 268:
            #     continue

            self.log.debug('regridding ugid: {0}'.format(ugid))
            predicate = partial(_pred_, ugid=[ugid])
            self.log.debug('creating single element shapefile')
            self.create_elements_shapefile(PATH_CATCHMENTS_SUBSET, single_element_shapefile, predicate)
            self.log.debug('creating ugrid')
            self.create_ugrid_netcdf(in_shp=single_element_shapefile, out_nc=out_ugrid_nc, name_uid=NAME_UID)
            self.log.debug('running get_dstfield')
            dstfield = get_dstfield(out_ugrid_nc, PATH_SYNTHETIC_SOURCE_DATA, self.log, debug=True)
            # tdk: this is the incorrect mean. there is an issue with esmf regridding at this time.
            self.assertAlmostEqual(dstfield.data.mean(), 365., places=2)
            dstfield.grid.destroy()
            dstfield.destroy()

            # tdk: RESUME: see if all single elements pass. then move on to the combinations...

    def test_subset_regridding_combinations(self):
        """Test regridding a subset of Texas catchments using different catchment combinations."""

        # self.set_debug(True)
        ESMF.Manager(debug=True)

        # path_source_data = os.path.join(self.path_bin, 'fake_data.nc')
        path_source_data = self.get_temporary_file_path('source_data.nc')
        # row = np.linspace(-0.876, 0.605)
        # col = np.linspace(-1.398, 0.662)
        row = None
        col = None
        field = self.get_ocgis_field()#col=col, row=row)
        grid_esmf = get_esmf_grid_from_sdim(field.spatial)
        self.create_source_netcdf_data(path_source_data, row=row, col=col)

        ocgis.env.DIR_OUTPUT = self.path_current_tmp
        ops = ocgis.OcgOperations(dataset={'uri': path_source_data}, snippet=True, output_format='shp')
        ops.execute()

        uid_name = 'UGID'

        subset_shp = os.path.join(self.path_bin, 'subset_catchments', 'catchment_singlepart_with_uid2.shp')

        def _pred_(record, ugid=None):
            if record['properties'][uid_name] in ugid:
                ret = True
            else:
                ret = False
            return ret

        out_shp = self.get_temporary_file_path('out.shp')
        out_ugrid_nc = self.get_temporary_file_path('catchment.nc')

        for combo in itertools.combinations([r['properties'][uid_name] for r in GeomCabinetIterator(path=subset_shp)], 2):
            # if combo[0] == 1 or (combo[0] == 2 and combo[1] < 39): continue
        # for r in GeomCabinetIterator(path=subset_shp):
        #     ugid = r['properties'][uid_name]
            self.log.info('regridding ugid: {0}'.format(combo))
            # predicate = partial(_pred_, ugid=[ugid])
            predicate = partial(_pred_, ugid=combo)
            self.log.debug('creating single element shapefile')
            self.create_elements_shapefile(subset_shp, out_shp, predicate)
            self.log.debug('single element shapefile: {0}'.format(out_shp))
            self.log.debug('creating ugrid')
            try:
                self.create_ugrid_netcdf(out_shp, out_ugrid_nc, name_uid=uid_name)
            except ValueError:
                self.log.error('ugrid conversion failed: {0}'.format(combo))
                # continue
                raise
            self.log.debug('running get_dstfield')
            try:
                dstfield = self.get_dstfield(path_source_data, out_ugrid_nc, debug=True, grid_esmf=grid_esmf)
            except ValueError:
                self.log.error('regridding failed: {0}'.format(combo))
                # continue
                raise
            else:
                self.assertAlmostEqual(dstfield.mean(), 1.0)
                self.assertEqual(dstfield.flatten().shape[0], len(combo))


