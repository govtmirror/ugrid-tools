#!/usr/bin/env bash

cd ~/src/pmesh && \
 git fetch && \
 git checkout i20-polygon-splitting && \
 git pull && \

bash /glade/u/home/benkoz/src/pmesh/sh/yellowstone/work.sh
