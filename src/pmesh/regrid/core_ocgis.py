import re
from os import listdir
from os.path import expanduser, join
from subprocess import check_output

import fiona
from logbook import INFO

from pmesh.helpers import nc_scope
from pmesh.logging import log
from pmesh.pyugrid.flexible_mesh.mpi import MPI_RANK, MPI_COMM, create_slices


def create_linked_shapefile(name_uid, output_variable, path_in_shp, path_linked_shp, path_output_data):
    with fiona.open(path_in_shp) as source:
        sink_meta = source.meta.copy()
        sink_meta['schema']['properties']['target'] = 'float'
        with fiona.open(path_linked_shp, mode='w', **sink_meta) as sink:
            with nc_scope(path_output_data) as output:
                for record in source:
                    uid = record['properties'][name_uid]
                    select = output.variables[name_uid][:] == uid
                    target_value = float(output.variables[output_variable][0, select][0])
                    record['properties']['target'] = target_value
                    sink.write(record)


if __name__ == '__main__':
    log.level = INFO
    name_uid = 'GRIDCODE'
    output_variable = 'pr'
    directory_shapefiles = expanduser('~/storage/catchment_shapefiles')
    directory_linked_shapefiles = expanduser('~/storage/linked_catchment_shapefiles')
    directory_weighted_data = expanduser('~/storage/catchment_weighted_data')

    if MPI_RANK == 0:
        weighted_data_files = filter(lambda x: x.startswith('pr_weighted'), listdir(directory_weighted_data))
        weighted_data_files = [weighted_data_files[slc[0]: slc[1]] for slc in create_slices(len(weighted_data_files))]
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

