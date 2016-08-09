#!/usr/bin/env bash

UTOOLS_ENV_SCRIPT=/glade/u/home/benkoz/src/ugrid-tools/sh/yellowstone/utools-env.sh
SRCDIR=/glade/u/home/benkoz/src/ugrid-tools

module reset
source ${UTOOLS_ENV_SCRIPT}

cd ${SRCDIR}
rm -r build
python setup.py build
