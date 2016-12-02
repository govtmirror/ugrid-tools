#!/usr/bin/env bash

# Check for required environment variables.
[ -z "${J}" ] && echo "Need to set J (the job name)" && exit 1
source ${UTOOLS_SRC}/sh/yellowstone/jobs/run-env.sh
[ -z "${YELLOWSTONE_PROJECT}" ] && echo "Need to set YELLOWSTONE_PROJECT" && exit 1

# Set additional environment variables dependent on the required environment variables.
source ${UTOOLS_SRC}/sh/yellowstone/jobs/run-env.sh

# Create the logging directories.
if [ -d ${LOG_DIR} ]; then
    echo "Logging directory must not exist: ${LOG_DIR}"
    exit 1
fi
mkdir -p ${LOG_DIR}/jobs && \
mkdir -p ${LOG_DIR}/esmf && \
mkdir -p ${UTOOLS_LOGGING_DIR}

# Generate weights.
bsub -J ${J} -o ${O} -e ${E} -P ${YELLOWSTONE_PROJECT} < ${JOB_DIR}/run-weight-gen.bsub
