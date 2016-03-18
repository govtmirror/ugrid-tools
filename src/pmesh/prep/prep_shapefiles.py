import os

import numpy as np
from netCDF4 import Dataset

from pmesh.logging import log_entry_exit, log
from pmesh.pyugrid.flexible_mesh.core import FlexibleMesh
from pmesh.pyugrid.flexible_mesh.helpers import convert_multipart_to_singlepart, flexible_mesh_to_esmf_format, \
    GeometryManager
from pmesh.pyugrid.flexible_mesh.mpi import MPI_RANK


def convert_to_singlepart():
    path_catchment_shp = '~/project/pmesh/bin/NHDPlusTX/NHDPlus12/NHDPlusCatchment/Catchment.shp'
    path_catchment_shp = os.path.expanduser(path_catchment_shp)
    path_output = os.path.expanduser('~/data/nfie_out')
    path_singlepart_shp = os.path.join(path_output, 'catchment_singlepart.shp')
    convert_multipart_to_singlepart(path_catchment_shp, path_singlepart_shp, new_uid_name='UGID')


def test_permissions():
    path = '/home/benkoziol/data/pmesh/nfie_out/foo.nc'
    ds = Dataset(path, 'w')
    ds.close()


@log_entry_exit
def convert_to_esmf_format(path_out_nc, path_in_shp, name_uid):
    polygon_break_value = -8

    log.debug('loading flexible mesh')
    fm = FlexibleMesh.from_shapefile(path_in_shp, name_uid, use_ragged_arrays=True, with_connectivity=False,
                                     allow_multipart=True)

    log.debug('writing flexible mesh')
    if MPI_RANK == 0:
        ds = Dataset(path_out_nc, 'w', format='NETCDF3_CLASSIC')
        try:
            flexible_mesh_to_esmf_format(fm, ds, polygon_break_value=polygon_break_value, face_uid_name=name_uid)
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


if __name__ == '__main__':
    # Run with MPI: mpirun -n 8 prep_shapefiles.py

    nfie_version = '20160314-0940'

    name_uid = 'GRIDCODE'
    storage_dir_shp = os.path.expanduser('~/storage/catchment_shapefiles')
    storage_dir_esmf = os.path.expanduser('~/storage/catchment_esmf_format')
    esmf_name_template = 'catchments_esmf_{cid}_{nfie_version}.nc'

    for catchment_directory in os.listdir(storage_dir_shp):
        for dirpath, dirnames, filenames in os.walk(os.path.join(storage_dir_shp, catchment_directory)):
            for fn in filenames:
                if fn.endswith('.shp'):
                    path_catchment_shp = os.path.join(dirpath, fn)
                    esmf_name = esmf_name_template.format(cid=catchment_directory, nfie_version=nfie_version)
                    path_esmf_format_nc = os.path.join(storage_dir_esmf, esmf_name)
                    log.info('Converting {}'.format(path_catchment_shp))
                    # log.debug((path_esmf_format_nc, path_catchment_shp, name_uid))
                    try:
                        convert_to_esmf_format(path_esmf_format_nc, path_catchment_shp, name_uid)
                    except:
                        log.exception(path_catchment_shp)
