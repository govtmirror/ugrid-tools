import functools
import os
import sys
import time

import logbook
from logbook import Logger, StreamHandler, FileHandler, INFO
from mpi4py import MPI

MPI_COMM = MPI.COMM_WORLD
MPI_RANK = MPI_COMM.Get_rank()


def formatter(record, handler):
    msg = '[{} {}]: {} (rank={}, time={}): {}'.format(record.channel, record.time, record.level_name, MPI_RANK,
                                                      time.time(), record.message)
    if record.level_name == 'ERROR':
        msg += '\n' + record.formatted_exception
    return msg


if 'PMESH_LOGGING_LEVEL' in os.environ:
    level = getattr(logbook, os.environ['PMESH_LOGGING_LEVEL'].upper())
else:
    level = INFO

log = Logger('pmesh', level=level)


if os.environ.get('PMESH_LOGGING_STDOUT', 'true').lower() != 'false':
    sh = StreamHandler(sys.stdout, bubble=True)
    sh.formatter = formatter
    # sh.format_string += ' (rank={})'.format(MPI_RANK)
    log.handlers.append(sh)
    # sh.push_application()

fh_directory = os.environ.get('PMESH_LOGGING_DIR', os.getcwd())
fh_file_prefix = os.environ.get('PMESH_LOGGING_FILE_PREFIX', 'pmesh')
fh = FileHandler(os.path.join(fh_directory, '{}-rank-{}.log'.format(fh_file_prefix, MPI_RANK)), bubble=True, mode='a')
fh.formatter = formatter
# fh.format_string += ' (rank={})'.format(MPI_RANK)
log.handlers.append(fh)


# fh.push_application()


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


def log_pmesh(level, msg, rank='all'):
    if rank != 'all' and MPI_RANK == rank:
        getattr(log, level)(msg)
