import os

import numpy as np
import pytest
from subprocess import check_output

from pmesh.prep.prep_shapefiles import convert_to_esmf_format
from pmesh.pyugrid.flexible_mesh.mpi import MPI_RANK, MPI_COMM
from pmesh.regrid.core_esmf import create_weights_file, created_weighted_output, validate_weighted_output
from pmesh.regrid.core_ocgis import create_linked_shapefile
from pmesh.test.base import AbstractNFIETest


class Test(AbstractNFIETest):

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
        created_weighted_output(path_in_esmf_format, path_in_source, path_out_weights_nc, path_output_data)

        validate_weighted_output(path_output_data)

    @pytest.mark.mpi_only
    @pytest.mark.mpi
    def test_create_weighted_output(self):
        path_esmf_format = os.path.join(self.path_bin, 'test_esmf_format.nc')
        path_weights_nc = os.path.join(self.path_bin, 'test_weights.nc')
        path_in_source = os.path.join(self.path_bin, 'precipitation_synthetic-20160310-1909.nc')

        if MPI_RANK == 0:
            path_output_data = self.get_temporary_file_path('weighted_esmf_format.nc')
        else:
            path_output_data = None

        path_output_data = MPI_COMM.bcast(path_output_data)

        created_weighted_output(path_esmf_format, path_in_source, path_weights_nc, path_output_data)

        if MPI_RANK == 0:
            validate_weighted_output(path_output_data)

        MPI_COMM.Barrier()

    def test_weighted_output(self):
        path_in_shp = os.path.join(self.path_bin, 'nhd_catchments_texas', 'nhd_catchments_texas.shp')
        name_uid = 'GRIDCODE'
        output_variable = 'pr'
        esmf_exe_path = check_output(['which', 'ESMF_RegridWeightGen']).strip()
        mpirun_exe_path = check_output(['which', 'mpirun']).strip()
        path_out_weights_nc = os.path.join(self.path_bin, 'test_weights.nc')
        path_in_source = os.path.join(self.path_bin, 'analytic_20160316-1627.nc')
        desired = [2266998.313787924, 2276969.734768346, 2274238.997428635, 2258694.7610502057, 2268728.548101572,
                         2270215.358892129, 2271532.4958518, 2273753.2226423565, 2273118.2178071104, 2273888.7447613683,
                         2271471.9927556557, 2267966.650649188, 2275582.2179131275, 2275301.37139591, 2272813.121773778,
                         2270663.719454991, 2267069.8546897713, 2259238.7995840707, 2262320.1334044924,
                         2261046.6661265413, 2252849.984781773, 2248750.841538354, 2255067.1315462627,
                         2257613.4306168156, 2256387.9716920396, 2251331.719429819, 2253716.4790673456,
                         2263096.887820415, 2255422.565794081, 2264155.619933094, 2258385.746916048, 2263216.5320504108,
                         2250298.59184182, 2265191.218025108, 2257913.4751813915, 2254372.936548597, 2260243.577475537,
                         2252852.035574644, 2257519.5523103094, 2263851.3695565723, 2258902.602869476,
                         2253839.982307549, 2259669.8989272225]

        path_output_data = self.get_temporary_file_path('weighted_esmf_format.nc')
        path_in_esmf_format = self.get_temporary_file_path('test_esmf_weights.nc')
        path_linked_shp = self.get_temporary_file_path('test_linked.shp')

        convert_to_esmf_format(path_in_esmf_format, path_in_shp, name_uid)
        create_weights_file(mpirun_exe_path, esmf_exe_path, path_in_source, path_in_esmf_format, path_out_weights_nc, n=1)
        created_weighted_output(path_in_esmf_format, path_in_source, path_out_weights_nc, path_output_data)

        create_linked_shapefile(name_uid, output_variable, path_in_shp, path_linked_shp, path_output_data)

        with self.nc_scope(path_output_data) as output:
            self.assertTrue(np.isclose(output.variables[output_variable][0, :], desired).all())
