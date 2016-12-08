#!/usr/bin/env bash

export J=nhd-exact-250m-regular-512-nc4
export BRANCH=dev-250m
export UTOOLS_SRC=/glade/u/home/benkoz/src/ugrid-tools
UTOOLS_SH=${UTOOLS_SRC}/sh/yellowstone/jobs/run.sh

cd ~/src/ugrid-tools && \
 git fetch && \
 git checkout ${BRANCH} && \
 git pull && \

echo "Job name is: ${J}"
bash ${UTOOLS_SH}
