import os
import re

import numpy as np
from logbook import DEBUG
from netCDF4 import Dataset

from utools.io.core import from_shapefile
from utools.io.helpers import convert_multipart_to_singlepart, convert_collection_to_esmf_format, GeometryManager
from utools.io.mpi import MPI_RANK
from utools.logging import log_entry_exit, log


def convert_to_singlepart():
    path_catchment_shp = '~/project/pmesh/bin/NHDPlusTX/NHDPlus12/NHDPlusCatchment/Catchment.shp'
    path_catchment_shp = os.path.expanduser(path_catchment_shp)
    path_output = os.path.expanduser('~/data/nfie_out')
    path_singlepart_shp = os.path.join(path_output, 'catchment_singlepart.shp')
    convert_multipart_to_singlepart(path_catchment_shp, path_singlepart_shp, new_uid_name='UGID')


@log_entry_exit
def convert_to_esmf_format(path_out_nc, path_in_shp, name_uid, node_threshold=None):
    polygon_break_value = -8

    log.debug('loading flexible mesh')
    coll = from_shapefile(path_in_shp, name_uid, use_ragged_arrays=True, with_connectivity=False, allow_multipart=True,
                          node_threshold=node_threshold)
    log.debug('writing flexible mesh')
    if MPI_RANK == 0:
        ds = Dataset(path_out_nc, 'w', format='NETCDF3_CLASSIC')
        try:
            convert_collection_to_esmf_format(coll, ds, polygon_break_value=polygon_break_value, face_uid_name=name_uid)
            validate_esmf_format(ds, name_uid, path_in_shp)
        finally:
            ds.close()
        log.debug('success')


@log_entry_exit
def validate_esmf_format(ds, name_uid, path_in_shp):
    # Confirm unique identifier is in fact unique.
    uid = ds.variables[name_uid][:]
    assert np.unique(uid).shape[0] == uid.shape[0]

    # Confirm each shapefile element is accounted for.
    assert ds.dimensions['elementCount'].size == len(GeometryManager(name_uid, path=path_in_shp))


def convert_shapefiles(pred=None, node_threshold=None):
    # Run with MPI: mpirun -n 8 prep_shapefiles.py

    nfie_version = 'node-threshold-10000'

    name_uid = 'GRIDCODE'
    storage_dir_shp = os.path.expanduser('/media/benkoziol/Extra Drive 1/data/nfie/linked_catchment_shapefiles')
    storage_dir_esmf = os.path.expanduser('/media/benkoziol/Extra Drive 1/data/nfie/node-thresholded-10000')
    esmf_name_template = 'esmf_format_{cid}_{nfie_version}.nc'

    log.info('Starting conversion for: {}'.format(nfie_version))

    for dirpath, dirnames, filenames in os.walk(os.path.join(storage_dir_shp, storage_dir_shp)):
        for fn in filenames:
            if fn.endswith('.shp'):
                log.debug(fn)
                if pred is not None and not pred(fn):
                    continue
                cid = re.search('linked_(.*).shp', fn).group(1)
                path_catchment_shp = os.path.join(dirpath, fn)
                esmf_name = esmf_name_template.format(cid=cid, nfie_version=nfie_version)
                path_esmf_format_nc = os.path.join(storage_dir_esmf, esmf_name)
                log.info('Converting {}'.format(path_catchment_shp))
                # log.debug((path_esmf_format_nc, path_catchment_shp, name_uid))
                try:
                    convert_to_esmf_format(path_esmf_format_nc, path_catchment_shp, name_uid,
                                           node_threshold=node_threshold)
                except:
                    log.exception(path_catchment_shp)


if __name__ == '__main__':
    # convert_shapefiles()
    log.level = DEBUG


    def f(filename):
        want = ['GreatLakes', 'SourisRedRainy', 'RioGrande', 'PacificNorthwest']
        ret = False
        for w in want:
            if w in filename:
                ret = True
                break
        return ret


    convert_shapefiles(pred=f, node_threshold=10000)
