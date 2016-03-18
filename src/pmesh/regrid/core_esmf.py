import os
import shutil
import subprocess

import numpy as np

from pmesh.helpers import nc_scope
from pmesh.logging import log, log_entry_exit
from pmesh.pyugrid.flexible_mesh.mpi import MPI_RANK, create_slices, MPI_COMM, MPI_SIZE


@log_entry_exit
def create_weights_file(mpirun_exe_path, esmf_exe_path, path_in_source, path_in_esmf_format, path_out_weights_nc, n=8):
    assert os.path.exists(path_in_source)
    assert os.path.exists(path_in_esmf_format)

    cmd = [mpirun_exe_path, '-n', str(n),
           esmf_exe_path, '-s', path_in_source, '-d', path_in_esmf_format, '-m', 'conserve',
           '--src_type', 'GRIDSPEC', '--dst_type', 'ESMF', '--src_regional', '-w', path_out_weights_nc]
    subprocess.check_call(cmd)


@log_entry_exit
def created_weighted_output(path_in_esmf_format, path_in_source, path_out_weights_nc, path_output_data):
    if MPI_RANK == 0:
        shutil.copy2(path_in_esmf_format, path_output_data)

        with nc_scope(path_out_weights_nc) as ds:
            length = ds.dimensions['n_b'].size
            slices = create_slices(length)
    else:
        slices = None

    section = MPI_COMM.scatter(slices, root=0)
    log.debug('section={}'.format(section))

    with nc_scope(path_in_source) as source:
        with nc_scope(path_out_weights_nc) as ds:
            row = ds.variables['row'][:]
            col = ds.variables['col'][:]
            S = ds.variables['S'][:]
            ntime = source.dimensions['time'].size
            voutput = np.zeros((ntime, section[1] - section[0]), dtype=float)
            for idx_voutput, idx_dst in enumerate(range(*section)):
                select = row == idx_dst + 1
                idx_src = col[select]
                s = S[select]
                # assert np.isclose(s.sum(), 1.0)
                for idx_time in range(source.dimensions['time'].size):
                    source_data = source.variables['pr'][idx_time, :, :].flatten()[idx_src]
                    weighted_data = np.dot(s, source_data)
                    voutput[idx_time, idx_voutput] = weighted_data

    if MPI_RANK == 0:
        with nc_scope(path_output_data, 'a') as output:
            with nc_scope(path_in_source) as source:
                output.createDimension('time')
                vtime = output.createVariable('time', source.variables['time'].dtype, dimensions=('time',))
                vtime.__dict__.update(source.variables['time'].__dict__)
                vtime[:] = source.variables['time'][:]
                output.createVariable('pr', float, dimensions=('time', 'elementCount'))

    for rank in range(MPI_SIZE):
        if rank == MPI_RANK:
            with nc_scope(path_output_data, 'a') as output:
                output.variables['pr'][:, section[0]:section[1]] = voutput
        MPI_COMM.Barrier()


@log_entry_exit
def validate_weighted_output(path_output_data):
    with nc_scope(path_output_data) as output:
        pr = output.variables['pr'][:]
        for idx_time in range(output.dimensions['time'].size):
            try:
                assert np.isclose(pr[idx_time].mean(), idx_time, 1e-4)
            except AssertionError:
                log.exception('mean={}, idx_time='.format(pr[idx_time].mean()), idx_time)
                raise


if __name__ == '__main__':
    n = 32
    mpirun_exe_path = '/home/ubuntu/miniconda2/envs/pmesh/bin/mpirun'
    esmf_exe_path = '/home/ubuntu/miniconda2/envs/pmesh/bin/ESMF_RegridWeightGen'
    path_in_source = os.path.expanduser('~/storage/analytic_data/analytic-conus_20160316-1737.nc')
    esmf_format_directory = os.path.expanduser('~/storage/catchment_esmf_format')
    output_data_directory = os.path.expanduser('~/storage/catchment_weighted_data')

    for fn in os.listdir(esmf_format_directory):
        if fn.endswith('.nc'):
            path_in_esmf_format = os.path.join(esmf_format_directory, fn)
            path_out_weights_nc = os.path.join(output_data_directory, 'weights-' + fn)
            path_output_data = os.path.join(output_data_directory, 'pr_weighted-' + fn)

            log.debug((mpirun_exe_path, esmf_exe_path, path_in_source, path_in_esmf_format, path_out_weights_nc, n))
            log.info('Operations for {}'.format(path_in_esmf_format))
            try:
                # log.info('start create_weights_file={}'.format(time.time()))
                # create_weights_file(mpirun_exe_path, esmf_exe_path, path_in_source, path_in_esmf_format, path_out_weights_nc, n=n)
                # log.info('stop create_weights_file={}'.format(time.time()))

                created_weighted_output(path_in_esmf_format, path_in_source, path_out_weights_nc, path_output_data)
            except:
                log.exception('Operation failed')

    log.info('core_esmf success')

