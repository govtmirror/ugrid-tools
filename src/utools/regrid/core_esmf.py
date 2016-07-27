import os
import shutil
import subprocess

import numpy as np

from utools.helpers import nc_scope
from utools.io.mpi import MPI_RANK, create_sections, MPI_COMM, MPI_SIZE
from utools.logging import log, log_entry_exit


@log_entry_exit
def create_weights_file(mpirun_exe_path, esmf_exe_path, path_in_source, path_in_esmf_format, path_out_weights_nc, n=8):
    # if mpirun_exe_path is not None:
    #     assert os.path.exists(mpirun_exe_path)
    # assert os.path.exists(esmf_exe_path)
    assert os.path.exists(path_in_source)
    assert os.path.exists(path_in_esmf_format)
    assert os.path.exists(os.path.split(path_out_weights_nc)[0])

    if mpirun_exe_path is None:
        cmd_mpi = []
    else:
        cmd_mpi = [mpirun_exe_path, '-n', str(n)]

    cmd = cmd_mpi + [esmf_exe_path, '-s', path_in_source, '-d', path_in_esmf_format, '-m', 'conserve',
           '--src_type', 'GRIDSPEC', '--dst_type', 'ESMF', '--src_regional', '-w', path_out_weights_nc]
    subprocess.check_call(cmd)


@log_entry_exit
def created_weighted_output(path_in_esmf_format, path_in_source, path_out_weights_nc, path_output_data, variable_name):
    if MPI_RANK == 0:
        log.info('Copying/creating output file')
        shutil.copy2(path_in_esmf_format, path_output_data)

        with nc_scope(path_out_weights_nc) as ds:
            length = len(ds.dimensions['n_b'])
            slices = create_sections(length)
    else:
        slices = None

    log.info('Applying weights')
    section = MPI_COMM.scatter(slices, root=0)
    log.debug('section={}'.format(section))

    with nc_scope(path_in_source) as source:
        with nc_scope(path_out_weights_nc) as ds:
            row = ds.variables['row'][:]
            col = ds.variables['col'][:]
            S = ds.variables['S'][:]
            ntime = len(source.dimensions['time'])
            voutput = np.zeros((ntime, section[1] - section[0]), dtype=float)
            for idx_voutput, idx_dst in enumerate(range(*section)):
                select = row == idx_dst + 1
                idx_src = col[select]
                s = S[select]
                # assert np.isclose(s.sum(), 1.0)
                for idx_time in range(len(source.dimensions['time'])):
                    source_data = source.variables[variable_name][idx_time, :, :].flatten()[idx_src]
                    weighted_data = np.dot(s, source_data)
                    voutput[idx_time, idx_voutput] = weighted_data

    log.info('Writing output file')
    if MPI_RANK == 0:
        log.info('Creating time dimension in output file')
        with nc_scope(path_output_data, 'a') as output:
            with nc_scope(path_in_source) as source:
                output.createDimension('time')
                vtime = output.createVariable('time', source.variables['time'].dtype, dimensions=('time',))
                vtime.__dict__.update(source.variables['time'].__dict__)
                vtime[:] = source.variables['time'][:]
                output.createVariable(variable_name, float, dimensions=('time', 'elementCount'))

    log.info('Fill output file by rank')
    for rank in range(MPI_SIZE):
        if rank == MPI_RANK:
            with nc_scope(path_output_data, 'a') as output:
                output.variables[variable_name][:, section[0]:section[1]] = voutput
        MPI_COMM.Barrier()


@log_entry_exit
def validate_weighted_output(path_output_data):
    with nc_scope(path_output_data) as output:
        pr = output.variables['pr'][:]
        for idx_time in range(len(output.dimensions['time'])):
            try:
                assert np.isclose(pr[idx_time].mean(), idx_time, 1e-4)
            except AssertionError:
                log.exception('mean={}, idx_time='.format(pr[idx_time].mean()), idx_time)
                raise


if __name__ == '__main__':
    n = 16
    mpirun_exe_path = '/glade/u/home/benkoz/miniconda2/envs/pmesh/bin/mpirun'
    esmf_exe_path = '/glade/u/home/benkoz/miniconda2/envs/pmesh/bin/ESMF_RegridWeightGen'
    path_in_source = os.path.expanduser('~/storage/exact_data/exact-conus-025degree_20160316-1737.nc')
    esmf_format_directory = os.path.expanduser('~/storage/catchment_esmf_format')
    output_data_directory = os.path.expanduser('~/storage/catchment_weighted_data')
    directory_catchment_shapefiles = os.path.expanduser('~/storage/catchment_shapefiles')

    # Regridding operations. ###########################################################################################
    # for fn in os.listdir(esmf_format_directory):
    #     if fn.endswith('.nc'):
    #         path_in_esmf_format = os.path.join(esmf_format_directory, fn)
    #         path_out_weights_nc = os.path.join(output_data_directory, 'weights-' + fn)
    #         path_output_data = os.path.join(output_data_directory, 'pr_weighted-' + fn)
    #
    #         log.debug((mpirun_exe_path, esmf_exe_path, path_in_source, path_in_esmf_format, path_out_weights_nc, n))
    #         log.info('Operations for {}'.format(path_in_esmf_format))
    #         try:
    #             log.info('start create_weights_file={}'.format(time.time()))
    #             create_weights_file(mpirun_exe_path, esmf_exe_path, path_in_source, path_in_esmf_format,
    #                                 path_out_weights_nc, n=n)
    #             log.info('stop create_weights_file={}'.format(time.time()))
    #
    #             # created_weighted_output(path_in_esmf_format, path_in_source, path_out_weights_nc, path_output_data)
    #         except:
    #             log.exception('Operation failed')

    # Validation for exact field. ######################################################################################

    # Add area variable to output data.
    # log.level = DEBUG
    # contents_esmf_format = os.listdir(esmf_format_directory)
    # contents_output_data = os.listdir(output_data_directory)
    # for catchment_uid in os.listdir(directory_catchment_shapefiles):
    #     for ce in contents_esmf_format:
    #         if catchment_uid in ce:
    #             for co in contents_output_data:
    #                 if catchment_uid in co and co.startswith('pr_weighted'):
    #                     path_esmf_format = os.path.join(esmf_format_directory, ce)
    #                     path_output_data = os.path.join(output_data_directory, co)
    #                     log.info('Adding area to {}'.format(path_output_data))
    #                     with nc_scope(path_output_data, 'a') as output:
    #                         with nc_scope(path_esmf_format, 'r') as input:
    #                             try:
    #                                 element_area = output.createVariable('elementArea', np.float32, ('elementCount',))
    #                             except RuntimeError:
    #                                 log.warn('Variable already created.')
    #                                 element_area = output.variables['elementArea']
    #                             element_area[:] = input.variables['elementArea'][:]
    #                             element_area.units = 'degrees'
    #                             element_area.long_name = 'Element area in native units.'

    # Calculate errors for exact field.
    # variable_name = 'pr'
    # ses = []
    # areas = []
    # for fn in os.listdir(output_data_directory):
    #     if fn.startswith('pr_weighted'):
    #         output = os.path.join(output_data_directory, fn)
    #         max_se = 1e-4
    #         max_rmse = 1e-4
    #         with nc_scope(output) as ds:
    #             exact_weighted = ds.variables[variable_name][0, :]
    #             coords = ds.variables['centerCoords'][:]
    #             areas += ds.variables['elementArea'][:].tolist()
    #         coords[:, 0] += 360.
    #         coords *= 0.0174533
    #         exact_centers = get_exact_field(coords[:, 1], coords[:, 0])
    #         se = (exact_weighted - exact_centers) ** 2
    #         ses += se.tolist()
    #
    # # This is for area weighting the errors. Very little effect observed.
    # # mse = np.average(ses, weights=(1 - np.array(areas)))
    # # This is standard mean error.
    # mse = np.mean(ses)
    # rmse = np.sqrt(mse)
    #
    # log.info('Element count={}'.format(len(ses)))
    # log.info('Max RSE={}'.format(np.array(np.sqrt(ses)).max()))
    # log.info('Min RSE={}'.format(np.array(np.sqrt(ses)).min()))
    # log.info('RMSE={}'.format(rmse))
    # log.info('NRMSE={}'.format(rmse / (exact_weighted.max() - exact_weighted.min())))
    #
    # log.info('core_esmf success')
