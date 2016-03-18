#!/usr/bin/env bash

echo '+++ Serial tests +++'
py.test --f -q -m 'not mpi_only' src
echo ''

echo '+++ MPI tests ++++++'
mpirun -n 8 py.test --f -q -m 'mpi' src

