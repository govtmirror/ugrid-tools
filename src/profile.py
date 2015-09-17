from cProfile import run
import cProfile
import os
from pstats import Stats
import tempfile
from ugrid import convert_multipart_to_singlepart, fiona_to_mesh2_nc
from ugrid.core import GeometryManager
from ugrid.helpers import create_rtree_file
from ugrid.mpi import MPI_RANK, MPI_COMM
from work_ocgis import area_weighted

profile_dat = os.path.expanduser('~/htmp/nfie/profile.dat')

def profile_target():
    area_weighted()


cProfile.run('profile_target()', filename=os.path.expanduser(profile_dat))
stats = Stats(profile_dat)
stats.strip_dirs()
stats.sort_stats('time', 'name')
stats.print_stats(0.05)
# stats.print_callers(0.05)