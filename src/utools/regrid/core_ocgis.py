import re
from os import listdir
from os.path import expanduser, join
from subprocess import check_output

import fiona
import numpy as np
from addict import Dict
from logbook import INFO
from ocgis import RequestDataset
from ocgis.new_interface.variable import VariableCollection, Variable

from utools.helpers import nc_scope
from utools.io.mpi import MPI_RANK, MPI_COMM, create_sections
from utools.logging import log


def create_linked_shapefile(name_uid, output_variable, path_in_shp, path_linked_shp, path_output_data):
    with fiona.open(path_in_shp) as source:
        sink_meta = source.meta.copy()
        sink_meta['schema']['properties'][output_variable] = 'float'
        with fiona.open(path_linked_shp, mode='w', **sink_meta) as sink:
            with nc_scope(path_output_data) as output:
                for record in source:
                    uid = record['properties'][name_uid]
                    select = output.variables[name_uid][:] == uid
                    target_value = float(output.variables[output_variable][0, select][0])
                    record['properties'][output_variable] = target_value
                    sink.write(record)


def create_merged_weights(weight_files, esmf_unstructured, master_weights):
    """
    Create a merged weight file containing some variables from the original ESMF mesh files.

    :param weight_files: sequence of file paths to the ESMF weight files
    :param esmf_unstructured:  sequence of file paths to the ESMF unstructured files (This sequence must be in the same
        order as ``weight_files``. The indexed weight file must have been created from the indexed ESMF unstructured.)
    :param master_weights: file path to the merged, master weights file
    """

    master_map = {}
    current_global_index = 1
    new_weight_file = Dict({'row': [], 'col': [], 'S': [], 'GRIDCODE': [], 'centerCoords': np.empty((0, 2))})
    new_dimensions = Dict({'row': 'n_s', 'col': 'n_s', 'S': 'n_s', 'GRIDCODE': 'elementCount',
                           'centerCoords': ('elementCount', 'coordDim')})
    new_dtype = {'row': np.int32, 'col': np.int32, 'S': np.float64}

    for uid, (w, e) in enumerate(zip(weight_files, esmf_unstructured)):
        log.info('Merge is processing weight file: {}'.format(w))
        log.info('Merge is processing ESMF unstructured file: {}'.format(e))
        w = RequestDataset(w).get()
        e = RequestDataset(e).get()

        for row_value in w['row'].value.flat:
            if row_value < 0:
                raise ValueError('"row" value must be greater than or equal to 1 to qualify as a Fortran index.')
            if (uid, row_value) not in master_map:
                master_map[(uid, row_value)] = current_global_index
                current_global_index += 1
            new_weight_file.row.append(master_map[(uid, row_value)])

        new_weight_file.col += w['col'].value.tolist()
        # new_weight_file.row += w['row'].value.tolist()
        new_weight_file.S += w['S'].value.tolist()

        new_weight_file.GRIDCODE += e['GRIDCODE'].value.tolist()
        new_weight_file.centerCoords = np.vstack((new_weight_file.centerCoords, e['centerCoords'].value))

    vc = VariableCollection()
    for k, v in new_weight_file.items():
        new_var = Variable(name=k, value=v, dimensions=new_dimensions[k], dtype=new_dtype.get(k))
        vc.add_variable(new_var)

    assert np.all(vc['row'].value >= 1)

    vc.attrs['coordDim'] = "longitude latitude"
    vc.attrs['description'] = "Merged ESMF weights file with auxiliary variables."

    vc['GRIDCODE'].attrs['long_name'] = 'Element unique identifier.'
    vc['centerCoords'].units = 'degrees'
    vc['row'].attrs['long_name'] = 'ESMF index to destination array.'
    vc['col'].attrs['long_name'] = 'ESMF index to source array.'
    vc['S'].attrs['long_name'] = 'ESMF weight factor.'

    vc.write(master_weights)


def run_create_linked_shapefile():
    log.level = INFO
    name_uid = 'GRIDCODE'
    output_variable = 'pr'
    directory_shapefiles = expanduser('~/storage/catchment_shapefiles')
    directory_linked_shapefiles = expanduser('~/storage/linked_catchment_shapefiles')
    directory_weighted_data = expanduser('~/storage/catchment_weighted_data')

    if MPI_RANK == 0:
        weighted_data_files = filter(lambda x: x.startswith('pr_weighted'), listdir(directory_weighted_data))
        weighted_data_files = [weighted_data_files[slc[0]: slc[1]] for slc in create_sections(len(weighted_data_files))]
    else:
        weighted_data_files = None

    weighted_data_files = MPI_COMM.scatter(weighted_data_files, root=0)

    for ii in weighted_data_files:
        path_output_data = join(directory_weighted_data, ii)
        # log.debug(ii)
        res = re.search('pr_weighted-catchments_esmf_(.*)_', ii).groups()[0]
        # log.debug(res.groups()[0])
        shapefile_directory = join(directory_shapefiles, res)
        path_in_shp = check_output(['find', shapefile_directory, '-name', '*Catchment.shp']).strip()
        path_linked_shp = join(directory_linked_shapefiles, 'linked_{}.shp'.format(res))
        log.debug((path_in_shp, path_linked_shp))
        log.info('Creating linked shapefile for: {}'.format(path_output_data))
        create_linked_shapefile(name_uid, output_variable, path_in_shp, path_linked_shp, path_output_data)


if __name__ == '__main__':
    pass
