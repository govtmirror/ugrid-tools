#!/usr/bin/env bash


#MPI_PROCS=1
MPI_PROCS=36
WD=~/htmp/logs

UTOOLS_CFG_PATH=/home/ubuntu/data/utools.cfg
UTOOLS_CONDA_ENV=ugrid-tools
UTOOLS_CLI=/home/ubuntu/project/ugrid-tools/src/utools_cli.py
UTOOLS_DEBUG='--no-debug'
UTOOLS_FEATURE_CLASS=Catchment
UTOOLS_GDB_PATH=/home/ubuntu/data/NHDPlusNationalData/NHDPlusV21_National_Seamless.gdb
UTOOLS_DEST_CRS_INDEX="National_Water_Model,crs_wkt"
#export UTOOLS_LOGGING_DIR=~/htmp
#export UTOOLS_LOGGING_LEVEL=DEBUG
export UTOOLS_LOGGING_ENABLED="true"
export UTOOLS_LOGGING_MODE="w"
export UTOOLS_LOGGING_TOFILE="true"
#export UTOOLS_LOGGING_STDOUT="true"
UTOOLS_OUTPUT_FILE=/home/ubuntu/htmp/ESMF_Unstructured_NHDPlusV21_National_Seamless_20160825_1026.nc
UTOOLS_SRC_DIR=/home/ubuntu/project/ugrid-tools/src
UTOOLS_SRC_UID="GRIDCODE"

#-----------------------------------------------------------------------------------------------------------------------

cd ${WD}

source activate ${UTOOLS_CONDA_ENV}
export PYTHONPATH=${UTOOLS_SRC_DIR}:${PYTHONPATH}

mpirun -n ${MPI_PROCS} python ${UTOOLS_CLI} convert -u ${UTOOLS_SRC_UID} -s ${UTOOLS_GDB_PATH} \
    -e ${UTOOLS_OUTPUT_FILE} --feature-class ${UTOOLS_FEATURE_CLASS} --config-path ${UTOOLS_CFG_PATH} \
    --dest_crs_index=${UTOOLS_DEST_CRS_INDEX} ${UTOOLS_DEBUG}
