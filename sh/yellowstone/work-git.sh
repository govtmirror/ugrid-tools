#!/usr/bin/env bash

cd ~/src/pmesh && \
 git fetch && \
 git checkout i20-single-vpu && \
 git pull && \

bash /glade/u/home/benkoz/src/pmesh/sh/yellowstone/work.sh
