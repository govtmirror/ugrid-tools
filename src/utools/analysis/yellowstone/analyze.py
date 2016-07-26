import os
import re
from os.path import join

from utools.analysis.yellowstone.db import VectorProcessingUnit, Session, setup_database, Timing, Job, get_or_create

log_dir = '/media/benkoziol/Extra Drive 1/yellowstone/logs'
pmesh_logs = join(log_dir, 'pmesh')


def fill_database():
    s = Session()

    for l in os.listdir(pmesh_logs):
        if 'rank-0' in l:
            catchment = re.search('weighting-(.+-.+)-rank', l)
            catchment = catchment.group(1)
            vpu = VectorProcessingUnit(name=catchment)
            s.add(vpu)

    for l in os.listdir(log_dir):
        if l.endswith('.out'):
            path = join(log_dir, l)
            job = Job.create(path)
            s.add(job)

    for l in os.listdir(pmesh_logs):
        if 'rank-0' in l:
            catchment = re.search('weighting-(.+-.+)-rank', l)
            catchment = catchment.group(1)

            vpu = get_or_create(s, VectorProcessingUnit, name=catchment)

            found = False
            for j in s.query(Job):
                if vpu.name in j.name and 'weight-gen' in j.name:
                    create_weights = j.run_time
                    found = True
                    break
            assert found

            path = join(pmesh_logs, l)
            t = Timing.create(path, vpu, create_weights)
            s.add(t)

    s.commit()


def report():
    s = Session()
    q = s.query(Timing)
    print '"Name" "Create Weights (Minutes)" "Apply Weights (Seconds)"'
    for t in q:
        print t.vpu.name, t.create_weights / 60., t.apply_weights_calculation


if __name__ == '__main__':
    setup_database()
    fill_database()
    report()
