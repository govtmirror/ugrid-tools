import os
from subprocess import check_output

import numpy as np

from utools.io.mpi import MPI_RANK, MPI_COMM
from utools.prep.create_netcdf_data import create_source_netcdf_data, get_exact_field
from utools.prep.prep_shapefiles import convert_to_esmf_format
from utools.regrid.core_esmf import create_weights_file, created_weighted_output, validate_weighted_output
from utools.regrid.core_ocgis import create_linked_shapefile
from utools.test.base import AbstractUToolsTest, attr


class Test(AbstractUToolsTest):

    def test_create_weights_file(self):
        path_in_source = os.path.join(self.path_bin, 'precipitation_synthetic-20160310-1909.nc')
        path_in_shp = os.path.join(self.path_bin, 'nhd_catchments_texas', 'nhd_catchments_texas.shp')
        name_uid = 'GRIDCODE'
        esmf_exe_path = check_output(['which', 'ESMF_RegridWeightGen']).strip()
        mpirun_exe_path = check_output(['which', 'mpirun']).strip()
        path_in_esmf_format = self.get_temporary_file_path('test_esmf_format.nc')
        path_out_weights_nc = self.get_temporary_file_path('test_weights.nc')
        path_output_data = self.get_temporary_file_path('weighted_esmf_format.nc')

        convert_to_esmf_format(path_in_esmf_format, path_in_shp, name_uid)
        create_weights_file(mpirun_exe_path, esmf_exe_path, path_in_source, path_in_esmf_format, path_out_weights_nc, n=8)
        created_weighted_output(path_in_esmf_format, path_in_source, path_out_weights_nc, path_output_data, 'pr')

        validate_weighted_output(path_output_data)

    @attr('mpi', 'mpi_only')
    def test_create_weighted_output(self):
        path_esmf_format = os.path.join(self.path_bin, 'test_esmf_format.nc')
        path_weights_nc = os.path.join(self.path_bin, 'test_weights.nc')
        path_in_source = os.path.join(self.path_bin, 'precipitation_synthetic-20160310-1909.nc')

        if MPI_RANK == 0:
            path_output_data = self.get_temporary_file_path('weighted_esmf_format.nc')
        else:
            path_output_data = None

        path_output_data = MPI_COMM.bcast(path_output_data)

        created_weighted_output(path_esmf_format, path_in_source, path_weights_nc, path_output_data, 'pr')

        if MPI_RANK == 0:
            validate_weighted_output(path_output_data)

        MPI_COMM.Barrier()

    def test_weighted_output(self):
        path_in_shp = os.path.join(self.path_bin, 'nhd_catchments_texas', 'nhd_catchments_texas.shp')
        name_uid = 'GRIDCODE'
        # esmf_exe_path = '/home/benkoziol/anaconda2/envs/pmesh/bin/ESMF_RegridWeightGen'
        esmf_exe_path = 'ESMF_RegridWeightGen'
        # mpirun_exe_path = '/home/benkoziol/anaconda2/envs/pmesh/bin/mpirun'
        mpirun_exe_path = 'mpirun'
        variable_name = 'exact'

        path_output_data = self.get_temporary_file_path('weighted_esmf_format.nc')
        path_in_esmf_format = self.get_temporary_file_path('test_esmf_weights.nc')
        path_linked_shp = self.get_temporary_file_path('test_linked.shp')
        path_out_weights_nc = self.get_temporary_file_path('output_weights_file.nc')
        path_src = self.get_temporary_file_path('exact.nc')

        # Test root mean squared error.
        row = np.arange(32.0012, 32.4288 + 0.01, 0.01)
        col = np.arange(-95.0477, -94.7965 + 0.01, 0.01)

        create_source_netcdf_data(path_src, row=row, col=col, exact=True, variable_name=variable_name)
        # OcgOperations(dataset={'uri': path_src}, snippet=True, output_format='shp', prefix='exact',
        #               dir_output=self.path_current_tmp).execute()

        convert_to_esmf_format(path_in_esmf_format, path_in_shp, name_uid)
        create_weights_file(mpirun_exe_path, esmf_exe_path, path_src, path_in_esmf_format, path_out_weights_nc, n=1)
        created_weighted_output(path_in_esmf_format, path_src, path_out_weights_nc, path_output_data, variable_name)

        create_linked_shapefile(name_uid, variable_name, path_in_shp, path_linked_shp, path_output_data)

        max_se = 1e-4
        max_rmse = 1e-4
        with self.nc_scope(path_output_data) as ds:
            exact = ds.variables[variable_name][0, :]
            coords = ds.variables['centerCoords'][:]
        coords[:, 0] += 360.
        coords *= 0.0174533
        exact_centers = get_exact_field(coords[:, 1], coords[:, 0])
        se = (exact - exact_centers) ** 2
        mse = np.mean(se)
        rmse = np.sqrt(mse)

        self.assertLessEqual(rmse, max_rmse)
        self.assertLessEqual(se.max(), max_se)
