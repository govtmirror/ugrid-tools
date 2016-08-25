#!/usr/bin/env bash


CARTESIAN_FILENAME=test_cartesian_grid_20160525.nc
DROPBOX_URL="https://www.dropbox.com/s/930cak3i51zhn6a/test_cartesian_grid_20160525.nc"


if [ ! -f ${CARTESIAN_FILENAME} ]; then
    wget ${DROPBOX_URL}
fi

ncdump -h ${CARTESIAN_FILENAME}

ESMF_RegridWeightGen -s ${CARTESIAN_FILENAME} -d ${CARTESIAN_FILENAME} -w tmp_weights.nc -m conserve -l cartesian \
    --src_regional --dst_regional --src_coordinates x,y --dst_coordinates x,y
