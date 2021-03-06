#!/usr/bin/env bash

[ -z "${J}" ] && echo "Need to set J (the job name)" && exit 1
source ${UTOOLS_SRC}/sh/yellowstone/jobs/run-env.sh

# Create the logging directory failing if it already exists.
if [ -d ${LOG_DIR} ]; then
    echo "Logging directory must not exist: ${LOG_DIR}"
    exit 1
fi
mkdir -p ${LOG_DIR}/jobs && \
mkdir -p ${LOG_DIR}/esmf && \
mkdir -p ${UTOOLS_LOGGING_DIR}
#mkdir -p ${ESMF_UGRID_DIR}

#idx=0
#for catchment_id in "${CATCHMENT_ID[@]}"
#do
#    j=${J_PREFIX}-${catchment_id}
#    wall_time=${W}
#    n=${N}
#    wall_time=${W[idx]}
#    n=${N[idx]}


#    export SHAPEFILE_SOURCE=${CATCHMENT_SHP[idx]}
#    export DESTINATION=${STORAGE}/catchment_esmf_format/node-thresholded-10000/esmf_format_${catchment_id}_node-threshold-10000.nc
#    export DESTINATION=${ESMF_UGRID_DIR}/esmf_format_${catchment_id}.nc
#    export DESTINATION=${ESMF_UGRID_DIR}/esmf_format_${catchment_id}.nc
#    export WEIGHTS=${STORAGE}/esmf_weights/esmf_weights_${catchment_id}.nc
#    export WEIGHTED_OUTPUT=${STORAGE}/scratch/output_weighted_${catchment_id}.nc

    # Convert catchments shapefile to ESMF format.
#    bsub -W ${wall_time} -n ${N} -J ${j}-convert-to-esmf -o ${o} -e ${e} < ${JOB_DIR}/run-convert-to-esmf.bsub

# Assert the unstructured grid file exists.
if [ ! -f ${ESMF_UGRID_FILENAME} ]; then
    echo "ESMF Unstructured format file not found."
    exit 1
fi

# Generate weights.
bsub -W ${W} -n ${N} -J ${J} -o ${O} -e ${E} -q ${q} -R ${R} < ${JOB_DIR}/run-weight-gen.bsub
#    bsub -w "done(${J}-convert-to-esmf)" -W ${W} -n ${N} -J ${J}-weight-gen < ${JOB_DIR}/run-weight-gen.bsub

    # Apply weights and create weighted output.
#    bsub -w "done(${j}-weight-gen)" -W "00:01" -n 128 -J ${j}-apply-weights -o ${o} -e ${e} < ${JOB_DIR}/run-apply-weights.bsub

#    idx=$((idx + 1))
#done
