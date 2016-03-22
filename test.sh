#!/usr/bin/env bash

echo '+++ Serial tests +++'
nosetests -q -a '!mpi_only' src && \
echo '' && \

echo '+++ MPI tests ++++++' && \
mpirun -n 8 nosetests -q -a 'mpi' src

