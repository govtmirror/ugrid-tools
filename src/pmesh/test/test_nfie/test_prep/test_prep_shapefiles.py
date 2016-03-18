import os

import pytest

from pmesh.prep.prep_shapefiles import convert_to_esmf_format
from pmesh.pyugrid.flexible_mesh.mpi import MPI_COMM, MPI_RANK
from pmesh.test.base import AbstractNFIETest


class Test(AbstractNFIETest):

    @pytest.mark.mpi
    def test_convert_to_esmf_format(self):
        path_in_shp = os.path.join(self.path_bin, 'nhd_catchments_texas', 'nhd_catchments_texas.shp')
        name_uid = 'GRIDCODE'
        path_out_nc = self.get_temporary_file_path('out.nc')
        convert_to_esmf_format(path_out_nc, path_in_shp, name_uid)

        if MPI_RANK == 0:
            with self.nc_scope(path_out_nc) as ds:
                self.assertEqual(len(ds.variables), 5)

        MPI_COMM.Barrier()
