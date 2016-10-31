#!/usr/bin/env bash

BRANCH=conus-spherical-exact-data

cd ~/src/ugrid-tools && \
 git fetch && \
 git checkout ${BRANCH} && \
 git pull && \

bash /glade/u/home/benkoz/src/ugrid-tools/sh/yellowstone/work.sh
