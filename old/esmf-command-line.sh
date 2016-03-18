#!/usr/bin/env bash


ESMF_BIN=/home/ubuntu/sandbox/esmf/bin/binO/Linux.gfortran.64.mpich2.default
DATA_SOURCE=precipitation_synthetic.nc
DATA_DESTINATION=catchment_ugrid.nc
OUTPUT_NETCDF_WEIGHTS=w.nc
TEST_DIR=/tmp/mesh-remapping-20151204
NP=4

########################################################################################################################

mkdir -p ${TEST_DIR}
cd ${TEST_DIR}
wget https://www.dropbox.com/s/zzmmumydq0kb8fi/catchment_ugrid.nc
wget https://www.dropbox.com/s/drnf0osf21do4ff/precipitation_synthetic.nc

mpirun -np ${NP} ${ESMF_BIN}/ESMF_RegridWeightGen -s ${DATA_SOURCE} --src_type GRIDSPEC --src_regional --dst_regional \
 -d ${DATA_DESTINATION} --dst_type UGRID -m conserve -w ${OUTPUT_NETCDF_WEIGHTS} --dst_meshname mesh


## Peggy test command ##################################################################################################

cd /tmp
source=/home/benkoziol/Dropbox/NESII/project/nfie/bin/precipitation_synthetic.nc
destination=/home/benkoziol/data/nfie/nfie_out/catchments_esmf_format_1d_20160302-1643.nc
rm PET*
date
mpirun -n 8 ESMF_RegridWeightGen -s ${source} -d ${destination} -m conserve -w test.nc --src_type GRIDSPEC -i --dst_type ESMF
date