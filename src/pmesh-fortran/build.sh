export PREFIX=/home/benkoziol/anaconda2/envs/pmesh-fortran
export WD=/home/benkoziol/l/project/pmesh/src/pmesh-fortran
#export PROGRAM_FILENAME=example_netcdf_read.f
export PROGRAM_FILENAME=read_factors.f

export LD_LIBRARY_PATH=${PREFIX}/lib
cd ${WD}

gfortran ${PROGRAM_FILENAME} -ffree-form -o /tmp/enr -I${PREFIX}/include -L${PREFIX}/lib -lnetcdff -L${PREFIX}/lib -lnetcdf -lnetcdf -L${PREFIX}/lib -lhdf5_hl -lhdf5 && \

/tmp/enr

#gfortran example_netcdf_read.f -o /tmp/enr `/home/benkoziol/anaconda2/envs/pmesh-fortran/bin/nf-config --fflags --flibs`
