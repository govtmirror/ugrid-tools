#!/usr/bin/env bash


#WD=/glade/u/home/benkoz/logs/esmf

#cd ~/logs/esmf && \
# bsub < /glade/u/home/benkoz/src/pmesh/sh/yellowstone/run-vpu.bsub && \
# watch -n 5 bjobs

#cd ${WD} && \

PMESH_SH=/glade/u/home/benkoz/src/pmesh/sh/yellowstone/jobs/run.sh
#PMESH_SH=/glade/u/home/benkoz/src/pmesh/sh/yellowstone/run-vpu.bsub
#PMESH_SH=/glade/u/home/benkoz/src/pmesh/sh/yellowstone/run-vpu-texas.bsub

bash ${PMESH_SH}

#bsub < ${PMESH_SH}

#bsub -n 40 -J "pmesh-2.0.1" < ${PMESH_SH}
#bsub -n 80 -J "pmesh-2.5.2" < ${PMESH_SH}
#bsub -n 120 -J "pmesh-2.2.1" < ${PMESH_SH}
#bsub -n 160 -J "pmesh-2.7.0" < ${PMESH_SH}