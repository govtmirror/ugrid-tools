#!/usr/bin/env bash

echo '+++ Serial tests +++'
py.test -q -m 'not mpi_only' src
echo ''

echo '+++ MPI tests ++++++'
mpirun -n 8 py.test -q -m 'mpi' src

