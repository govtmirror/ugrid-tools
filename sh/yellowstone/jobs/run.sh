#!/usr/bin/env bash

[ -z "${J_PREFIX}" ] && echo "Need to set J_PREFIX (the job name prefix)" && exit 1

CATCHMENT_ID=( 03W-SouthAtlanticWest 10L-LowerMissouri 11-ArkRedWhite 02-MidAtlantic 04-GreatLakes 05-Ohio 10U-UpperMissouri 01-Northeast 08-LowerMississippi 12-Texas 03N-SouthAtlanticNorth 06-Tennessee 14-UpperColorado 18-California 03S-SouthAtlanticSouth 15-LowerColorado 16-GreatBasin 07-UpperMississippi 09-SourisRedRainy 13-RioGrande 17-PacificNorthwest )
#CATCHMENT_ID=( 13-RioGrande 17-PacificNorthwest )
W=( 00:04 00:07 00:07 00:04 00:17 00:04 00:11 00:06 00:04 00:11 00:04 00:03 00:04 00:09 00:05 00:05 00:11 00:04 00:25 02:14 01:26 )
#W=( 03:00 02:00 )
N=256
JOB_DIR=/glade/u/home/benkoz/src/pmesh/sh/yellowstone/jobs
STORAGE=/glade/p/work/benkoz/storage

export PYTHONPATH=${PYTHONPATH}:/glade/u/home/benkoz/src/click/build/lib:/glade/u/home/benkoz/src/logbook/build/lib
#export PYTHONPATH=${PYTHONPATH}:/glade/u/home/benkoz/src/click/build/lib:/glade/u/home/benkoz/src/logbook/build/lib:/glade/u/home/benkoz/src/click-plugins/build/lib:/glade/u/home/benkoz/src/Fiona/build/lib.linux-x86_64-2.7
#export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/glade/apps/opt/gdal/1.10.0/intel/default/lib:/glade/apps/opt/netcdf/4.3.0/intel/12.1.5/lib:/glade/apps/opt/hdf5/1.8.9/intel/12.1.4/lib

export LOG_DIR=/glade/u/home/benkoz/logs/${J_PREFIX}
export ESMF_EXE=/glade/u/home/benkoz/sandbox/esmf_HEAD/bin/ESMF_RegridWeightGen
export PMESH_CLI=/glade/u/home/benkoz/src/pmesh/src/pmesh_cli.py
export PMESH_LOGGING_DIR=${LOG_DIR}/pmesh
export PMESH_LOGGING_LEVEL=info
export PMESH_LOGGING_STDOUT=false
export SHAPEFILE_UID=GRIDCODE
export SOURCE=${STORAGE}/exact_data/exact-conus-025degree_20160316-1737.nc
export VARIABLE_NAME=pr
o="${LOG_DIR}/jobs/pmesh.%J.out"
e="${LOG_DIR}/jobs/pmesh.%J.err"

# Create the logging directory failing if it already exists.
if [ -d ${LOG_DIR} ]; then
    echo "Logging directory must not exist: ${LOG_DIR}"
    exit 1
fi
mkdir -p ${LOG_DIR}/jobs
mkdir -p ${LOG_DIR}/esmf
mkdir -p ${PMESH_LOGGING_DIR}

idx=0
for catchment_id in "${CATCHMENT_ID[@]}"
do
    j=${J_PREFIX}-${catchment_id}
#    wall_time=${W}
    n=${N}
    wall_time=${W[idx]}
#    n=${N[idx]}

    export PMESH_LOGGING_FILE_PREFIX=${j}
    export SHAPEFILE_SOURCE=${STORAGE}/catchment_shapefiles/linked_${catchment_id}.shp
    export DESTINATION=${STORAGE}/catchment_esmf_format/catchments_esmf_${catchment_id}_v0.1.0.dev1-run2.nc
    #export DESTINATION=/glade/u/home/benkoz/storage/scratch/esmf_format_${CATCHMENT_ID}.nc
    export WEIGHTS=${STORAGE}/scratch/weights_${catchment_id}.nc
    export WEIGHTED_OUTPUT=${STORAGE}/scratch/output_weighted_${catchment_id}.nc

    # Convert catchments shapefile to ESMF format.
    #bsub -W ${W} -n ${N} -J ${J}-convert-to-esmf -o ${o} -e ${e} < ${JOB_DIR}/run-convert-to-esmf.bsub

    # Generate weights.
    bsub -W ${wall_time} -n ${n} -J ${j}-weight-gen -o ${o} -e ${e} < ${JOB_DIR}/run-weight-gen.bsub
    #bsub -w "done(${J}-convert-to-esmf)" -W ${W} -n ${N} -J ${J}-weight-gen < ${JOB_DIR}/run-weight-gen.bsub

    # Apply weights and create weighted output.
    bsub -w "done(${j}-weight-gen)" -W "00:01" -n 128 -J ${j}-apply-weights -o ${o} -e ${e} < ${JOB_DIR}/run-apply-weights.bsub

    idx=$((idx + 1))
done
