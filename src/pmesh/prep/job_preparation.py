"""Helps make job variables for supercomputer runs."""
from csv import DictReader

import numpy as np

JOBS_CSV = '/home/benkoziol/Dropbox/NESII/project/pmesh/office/Applying Weights.csv'

job_name = []
wall_times = []

with open(JOBS_CSV) as f:
    d = DictReader(f)
    for row in d:
        if row['Active'] == '1':
            job_name.append(row['Name'])
            wall_time = float(row['Create Weights (Minutes, 128 Cores)'])
            wall_time += 2.5
            wall_time = int(np.ceil(wall_time))
            if wall_time < 60:
                len_wall_time = len(str(wall_time))
                if len_wall_time == 1:
                    template = '00:0{}'
                elif len_wall_time == 2:
                    template = '00:{}'
                wall_time = template.format(wall_time)
            else:
                hours = int(np.floor(int(wall_time) / 60.))
                minutes = int(wall_time) - (hours * 60)
                wall_time = '0{hours}:{minutes}'.format(hours=hours, minutes=minutes)
            wall_times.append(wall_time)

assert len(job_name) == len(wall_times)

for arr in [job_name, wall_times]:
    joined = ' '.join(arr)
    joined = '( {} )'.format(joined)
    print joined
