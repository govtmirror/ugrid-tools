"""Test writing to a netCDF4 variable using MPI."""
from mpi4py import MPI

import numpy as np

from fmtools.test.base import AbstractFMToolsTest

COMM = MPI.COMM_WORLD
SIZE = COMM.Get_size()
STATUS = MPI.Status()
RANK = COMM.Get_rank()


class Test(AbstractFMToolsTest):

    def test(self):
        name_var = 'pr'
        ntime = 3
        nfaces = SIZE * 5
        path = None
        slices = None

        if RANK == 0:
            path = self.get_temporary_file_path('out.nc')

            with self.nc_scope(path, 'w') as ds:
                update_netcdf_dataset(ds, ntime, nfaces, name_var)

            self.nc_dump(path)

            slices = create_slices(nfaces)

        path = COMM.bcast(path, root=0)
        slc = COMM.scatter(slices, root=0)

        data = np.ones((ntime, slc[1] - slc[0])) * RANK

        if RANK != 0:
            COMM.recv(None, source=RANK - 1)

        with self.nc_scope(path, 'a') as ds:
            var = ds.variables[name_var]
            var[:, slc[0]:slc[1]] = data

        if RANK + 1 <= SIZE - 1:
            COMM.send(None, dest=RANK + 1)

        COMM.barrier()

        if RANK == 0:
            self.nc_dump(path, header=False)


def create_slices(length, size=SIZE):
    step = int(np.ceil(float(length) / size))
    indexes = [None] * size
    start = 0
    for ii in range(size):
        stop = start + step
        if stop > length:
            stop = length
        index_element = [start, stop]
        indexes[ii] = index_element
        start = stop
    return indexes


def update_netcdf_dataset(ds, ntime, nfaces, name_var):
    dtime = ds.createDimension('time', ntime)
    dfaces = ds.createDimension('face_count', nfaces)
    ds.createVariable(name_var, float, (dtime.name, dfaces.name))
