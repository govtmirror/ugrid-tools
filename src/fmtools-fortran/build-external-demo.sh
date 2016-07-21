#!/usr/bin/env bash

demo=ESMF_RegridWeightGenCheck
#demo=ESMF_ArraySMMStore

export ESMFMKFILE=/home/benkoziol/anaconda2/envs/esmf/lib/esmf.mk
#WD=/home/benkoziol/l/project/esmf-external_demos/ESMF_Regrid
WD=/home/benkoziol/l/project/esmf-external_demos/ESMF_RegridWeightGenCheck
#WD=/home/benkoziol/l/project/esmf-external_demos/ESMF_ArraySMMStore
#WD=/home/benkoziol/l/project/esmf-external_demos/Reproducer_ArrayGather
#WD=/home/benkoziol/l/project/esmf-external_demos/ESMF_FieldSMMStore
EXE=./ESMF_ArraySMMStore
#EXE=./Reproducer_ArrayGather
#EXE=./ESMF_FieldSMMStore
#EXE=./ESMF_Regrid

#source activate pmesh-fortran
source activate esmf
cd ${WD}
make clean
make
mpirun -n 8 ${EXE}
#${EXE}
