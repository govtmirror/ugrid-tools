import functools
import os
import sys
import tempfile

from logbook import Logger, StreamHandler, FileHandler, INFO
from mpi4py import MPI

MPI_COMM = MPI.COMM_WORLD
MPI_RANK = MPI_COMM.Get_rank()

sh = StreamHandler(sys.stdout, bubble=True)
sh.format_string += ' (rank={})'.format(MPI_RANK)
sh.push_application()

fh = FileHandler(os.path.join(tempfile.gettempdir(), 'pmesh-rank-{}.log'.format(MPI_RANK)), bubble=True, mode='w')
fh.format_string += ' (rank={})'.format(MPI_RANK)
fh.push_application()

log = Logger('pmesh', level=INFO)


class log_entry_exit(object):
    def __init__(self, f):
        self.f = f

    def __call__(self, *args, **kwargs):
        log.debug("entering {0})".format(self.f.__name__))
        try:
            return self.f(*args, **kwargs)
        finally:
            log.debug("exited {0})".format(self.f.__name__))

    def __get__(self, obj, _):
        """Support instance methods."""

        return functools.partial(self.__call__, obj)
