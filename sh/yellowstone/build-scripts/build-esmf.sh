#!/bin/bash

export PREFIX=/glade/u/home/benkoz/sandbox/esmf_HEAD
export CPU_COUNT=1
export ESMF_DIR=/glade/u/home/benkoz/src/esmf

#cd ~/src && \
#git clone git://git.code.sf.net/p/esmf/esmf
cd ~/src/esmf && \
# git checkout master && \
# git pull

#rm -r ${PREFIX}

#module swap intel gnu

export ESMF_INSTALL_PREFIX=${PREFIX}
export ESMF_INSTALL_BINDIR=${PREFIX}/bin
export ESMF_INSTALL_DOCDIR=${PREFIX}/doc
export ESMF_INSTALL_HEADERDIR=${PREFIX}/include
export ESMF_INSTALL_LIBDIR=${PREFIX}/lib
export ESMF_INSTALL_MODDIR=${PREFIX}/mod
export ESMF_NETCDF="split"
export ESMF_COMM=mpich2
#export ESMF_NETCDF_INCLUDE=${PREFIX}/include
#export ESMF_NETCDF_LIBPATH=${PREFIX}/lib

make clean
make -j ${CPU_COUNT}
#make check
#make all_tests | tee ~/esmf_all_tests.out
make install
