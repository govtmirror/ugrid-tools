#!/usr/bin/env bash

STORAGE=/glade/p/work/benkoz/storage

export LOG_DIR=/glade/u/home/benkoz/logs/${J}
export O="${LOG_DIR}/jobs/utools.%J.out"
export E="${LOG_DIR}/jobs/utools.%J.err"
export UTOOLS_SRCDIR=/glade/u/home/benkoz/src/ugrid-tools
export UTOOLS_BUILDDIR=${UTOOLS_SRCDIR}/build
export UTOOLS_CLI=utools_cli
export UTOOLS_LOGGING_DIR=${LOG_DIR}/utools
#export UTOOLS_LOGGING_LEVEL=info
export UTOOLS_LOGGING_FILE_PREFIX=${J}
export UTOOLS_LOGGING_STDOUT=false
export UTOOLS_LOGGING_ENABLED=true
export UTOOLS_ENV=${UTOOLS_SRCDIR}/sh/yellowstone/utools-env.sh
export JOB_DIR=${UTOOLS_SRCDIR}/sh/yellowstone/jobs
export NODE_THRESHOLD=5000
export VARIABLE_NAME=pr
