import cProfile
import os
from pstats import Stats

from misc.work_ocgis import area_weighted

profile_dat = os.path.expanduser('~/htmp/pmesh/profile.dat')

def profile_target():
    area_weighted()


cProfile.run('profile_target()', filename=os.path.expanduser(profile_dat))
stats = Stats(profile_dat)
stats.strip_dirs()
stats.sort_stats('time', 'name')
stats.print_stats(0.05)
# stats.print_callers(0.05)