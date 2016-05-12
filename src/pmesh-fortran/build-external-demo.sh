#!/usr/bin/env bash


export ESMFMKFILE=/home/benkoziol/anaconda2/envs/pmesh-fortran/lib/esmf.mk
#WD=/home/benkoziol/l/project/esmf-external_demos/ESMF_Regrid
WD=/home/benkoziol/l/project/esmf-external_demos/ESMF_ArraySMMStore
#WD=/home/benkoziol/l/project/esmf-external_demos/ESMF_FieldSMMStore
EXE=./ESMF_ArraySMMStore
#EXE=./ESMF_FieldSMMStore
#EXE=./ESMF_Regrid

source activate pmesh-fortran
cd ${WD}
make clean
make
mpirun -n 8 ${EXE}
#${EXE}
