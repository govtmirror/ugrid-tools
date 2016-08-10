#!/usr/bin/env bash

UTOOLS_ENV_SCRIPT=${UTOOLS_SRCDIR}/sh/yellowstone/utools-env.sh

module reset
source ${UTOOLS_ENV_SCRIPT}

cd ${UTOOLS_SRCDIR}
rm -r build
python setup.py build
