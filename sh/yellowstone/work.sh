#!/usr/bin/env bash


#WD=/glade/u/home/benkoz/logs/esmf

#cd ~/logs/esmf && \
# bsub < /glade/u/home/benkoz/src/utools/sh/yellowstone/run-vpu.bsub && \
# watch -n 5 bjobs

#cd ${WD} && \

UTOOLS_SH=/glade/u/home/benkoz/src/utools/sh/yellowstone/jobs/run.sh
#UTOOLS_SH=/glade/u/home/benkoz/src/utools/sh/yellowstone/run-vpu.bsub
#UTOOLS_SH=/glade/u/home/benkoz/src/utools/sh/yellowstone/run-vpu-texas.bsub

bash ${UTOOLS_SH}

#bsub < ${UTOOLS_SH}

#bsub -n 40 -J "utools-2.0.1" < ${UTOOLS_SH}
#bsub -n 80 -J "utools-2.5.2" < ${UTOOLS_SH}
#bsub -n 120 -J "utools-2.2.1" < ${UTOOLS_SH}
#bsub -n 160 -J "utools-2.7.0" < ${UTOOLS_SH}