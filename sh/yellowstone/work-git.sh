#!/usr/bin/env bash

cd ~/src/ugrid-tools && \
 git fetch && \
 git checkout yellowstone-convert-to-esmf && \
 git pull && \

bash /glade/u/home/benkoz/src/ugrid-tools/sh/yellowstone/work.sh
