#!/usr/bin/env bash

#W=( 00:30  )
#N=10
#N=2560
N=128
STORAGE=/glade/p/work/benkoz/storage
W=02:00
R="span[ptile=2]"
#R="span[ptile=40]"
q="regular"
#q="geyser"
#q="bigmem"

#export PYTHONPATH=${PYTHONPATH}:/glade/u/home/benkoz/src/click/build/lib:/glade/u/home/benkoz/src/logbook/build/lib:/glade/u/home/benkoz/src/addict/build/lib
#export PYTHONPATH=${PYTHONPATH}:/glade/u/home/benkoz/src/click/build/lib:/glade/u/home/benkoz/src/logbook/build/lib:/glade/u/home/benkoz/src/click-plugins/build/lib:/glade/u/home/benkoz/src/Fiona/build/lib.linux-x86_64-2.7
#export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/glade/apps/opt/gdal/1.10.0/intel/default/lib:/glade/apps/opt/netcdf/4.3.0/intel/12.1.5/lib:/glade/apps/opt/hdf5/1.8.9/intel/12.1.4/lib

export LOG_DIR=/glade/u/home/benkoz/logs/${J}
O="${LOG_DIR}/jobs/utools.%J.out"
E="${LOG_DIR}/jobs/utools.%J.err"
export ESMF_EXE=/glade/u/home/benkoz/sandbox/esmf_HEAD/bin/ESMF_RegridWeightGen
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
#export SHAPEFILE_UID=GRIDCODE
#export ESMF_UGRID_DIR=${STORAGE}/esmf_unstructured/node-threshold-${NODE_THRESHOLD}
export SOURCE=${STORAGE}/exact_data/high_resolution_ucar_exact_data_20160811.nc
#export SOURCE=${STORAGE}/exact_data/exact-conus-025degree_20160316-1737.nc
export VARIABLE_NAME=pr

export ESMF_UGRID_FILENAME=${STORAGE}/esmf_unstructured/ESMF_Unstructured_Spherical_NHDPlusV21_National_Seamless_20160825_1505.nc
export ESMF_WEIGHTS_FILENAME=${STORAGE}/esmf_weights/ESMF_Weights_Spherical_NHDPlusV21_National_Seamless_${J}.nc

#CATCHMENT_ID=( \
#07-UpperMississippi \
#10U-UpperMissouri \
#18-California \
#01-Northeast \
#12-Texas \
#15-LowerColorado \
#03W-SouthAtlanticWest \
#17-PacificNorthwest \
#06-Tennessee \
#02-MidAtlantic \
#04-GreatLakes \
#11-ArkRedWhite \
#10L-LowerMissouri \
#09-SourisRedRainy \
#13-RioGrande \
#05-Ohio \
#08-LowerMississippi \
#03S-SouthAtlanticSouth \
#14-UpperColorado \
#16-GreatBasin \
#03N-SouthAtlanticNorth \
#)

#CATCHMENT_SHP_DIR=/glade/u/home/benkoz/storage/catchment_shapefiles
#CATCHMENT_SHP=( \
#${CATCHMENT_SHP_DIR}/07-UpperMississippi/NHDPlusMS/NHDPlus07/NHDPlusCatchment/Catchment.shp \
#${CATCHMENT_SHP_DIR}/10U-UpperMissouri/NHDPlusMS/NHDPlus10U/NHDPlusCatchment/Catchment.shp \
#${CATCHMENT_SHP_DIR}/18-California/NHDPlusCA/NHDPlus18/NHDPlusCatchment/Catchment.shp \
#${CATCHMENT_SHP_DIR}/01-Northeast/NHDPlusNE/NHDPlus01/NHDPlusCatchment/Catchment.shp \
#${CATCHMENT_SHP_DIR}/12-Texas/NHDPlusTX/NHDPlus12/NHDPlusCatchment/Catchment.shp \
#${CATCHMENT_SHP_DIR}/15-LowerColorado/NHDPlusCO/NHDPlus15/NHDPlusCatchment/Catchment.shp \
#${CATCHMENT_SHP_DIR}/03W-SouthAtlanticWest/NHDPlusSA/NHDPlus03W/NHDPlusCatchment/Catchment.shp \
#${CATCHMENT_SHP_DIR}/17-PacificNorthwest/NHDPlusPN/NHDPlus17/NHDPlusCatchment/Catchment.shp \
#${CATCHMENT_SHP_DIR}/06-Tennessee/NHDPlusMS/NHDPlus06/NHDPlusCatchment/Catchment.shp \
#${CATCHMENT_SHP_DIR}/02-MidAtlantic/NHDPlusMA/NHDPlus02/NHDPlusCatchment/Catchment.shp \
#${CATCHMENT_SHP_DIR}/04-GreatLakes/NHDPlusGL/NHDPlus04/NHDPlusCatchment/Catchment.shp \
#${CATCHMENT_SHP_DIR}/11-ArkRedWhite/NHDPlusMS/NHDPlus11/NHDPlusCatchment/Catchment.shp \
#${CATCHMENT_SHP_DIR}/10L-LowerMissouri/NHDPlusMS/NHDPlus10L/NHDPlusCatchment/Catchment.shp \
#${CATCHMENT_SHP_DIR}/09-SourisRedRainy/NHDPlusSR/NHDPlus09/NHDPlusCatchment/Catchment.shp \
#${CATCHMENT_SHP_DIR}/13-RioGrande/NHDPlusRG/NHDPlus13/NHDPlusCatchment/Catchment.shp \
#${CATCHMENT_SHP_DIR}/05-Ohio/NHDPlusMS/NHDPlus05/NHDPlusCatchment/Catchment.shp \
#${CATCHMENT_SHP_DIR}/08-LowerMississippi/NHDPlusMS/NHDPlus08/NHDPlusCatchment/Catchment.shp \
#${CATCHMENT_SHP_DIR}/03S-SouthAtlanticSouth/NHDPlusSA/NHDPlus03S/NHDPlusCatchment/Catchment.shp \
#${CATCHMENT_SHP_DIR}/14-UpperColorado/NHDPlusCO/NHDPlus14/NHDPlusCatchment/Catchment.shp \
#${CATCHMENT_SHP_DIR}/16-GreatBasin/NHDPlusGB/NHDPlus16/NHDPlusCatchment/Catchment.shp \
#${CATCHMENT_SHP_DIR}/03N-SouthAtlanticNorth/NHDPlusSA/NHDPlus03N/NHDPlusCatchment/Catchment.shp \
#)

#CATCHMENT_ID=( 03W-SouthAtlanticWest 10L-LowerMissouri 11-ArkRedWhite 02-MidAtlantic 04-GreatLakes 05-Ohio 10U-UpperMissouri 01-Northeast 08-LowerMississippi 12-Texas 03N-SouthAtlanticNorth 06-Tennessee 14-UpperColorado 18-California 03S-SouthAtlanticSouth 15-LowerColorado 16-GreatBasin 07-UpperMississippi 09-SourisRedRainy 13-RioGrande 17-PacificNorthwest )
#CATCHMENT_ID=( 14-UpperColorado )
#CATCHMENT_SHP=( /glade/u/home/benkoz/storage/catchment_shapefiles/14-UpperColorado/NHDPlusCO/NHDPlus14/NHDPlusCatchment/Catchment.shp )

# Wall times for ESMF unstructured file generation.
#W=( 00:05 00:15 00:05 00:05 00:05 00:05 00:05 00:15 00:05 00:05 00:05 00:05 00:05 00:05 00:05 00:05 00:05 00:05 00:05 00:05 00:05 )

# Wall times for weight file generation.
#W=( 00:15 )
#W=( 00:15 00:15 00:15 00:15 00:15 00:15 00:15 00:15 00:15 00:15 00:15 00:15 00:15 00:15 00:15 00:15 00:15 00:15 00:15 00:15 00:15 )
