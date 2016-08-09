#!/usr/bin/env bash


#module rm netcdf

module swap intel gnu

module load python/2.7.7
module load gdal/2.0.2
module load shapely/1.5.16
module load numpy/1.11.0
module load netcdf4python/1.2.4
module load cython/0.23.4
module load mpi4py/2.0.0
module load fiona/1.7.0.p2
module load logbook

export PYTHONPATH=/glade/u/home/benkoz/src/ugrid-tools/build/lib:${PYTHONPATH}
export PATH=/glade/u/home/benkoz/src/ugrid-tools/build/scripts-2.7:${PATH}
