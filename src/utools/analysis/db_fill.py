import os
import re
from os.path import join

from ocgis import CoordinateReferenceSystem
from ocgis.util.geom_cabinet import GeomCabinetIterator

from utools.analysis.db import Session, VectorProcessingUnit, Shapefile, Catchment, Job, drop_create, get_or_create, \
    Timing
from utools.logging import log

SHAPEFILE_DIRECTORY = '/media/benkoziol/Extra Drive 1/data/nfie/storage/catchment_shapefiles'


def fill_database():
    s = Session()

    # VectorProcessingUnit, Shapefile ##################################################################################

    for d in os.listdir(SHAPEFILE_DIRECTORY):
        vpu = VectorProcessingUnit(name=d)
        s.add(vpu)
        s.add(Shapefile.create(vpu, join(SHAPEFILE_DIRECTORY, d)))

    # Catchment ########################################################################################################

    to_crs = CoordinateReferenceSystem(epsg=3083)
    for shapefile in s.query(Shapefile):
        log.info('Loading shapefile: {}'.format(shapefile.vpu.name))
        gi = GeomCabinetIterator(path=shapefile.fullpath)
        for record in gi:
            catchment = Catchment.create(shapefile.vpu, record, to_crs)
            s.add(catchment)
        s.commit()

    s.commit()


def parse_job(log_dir, cores):
    pmesh_logs = join(log_dir, 'pmesh')
    job_logs = join(log_dir, 'jobs')

    s = Session()

    for l in os.listdir(job_logs):
        if l.endswith('.out'):
            path = join(job_logs, l)
            job = Job.create(cores, path)
            s.add(job)

    for l in os.listdir(pmesh_logs):
        if 'rank-0' in l:
            catchment = re.search('test-all-256-cores-(.+-.+)-rank-0', l)
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
    rows = [['Vector Processing Unit', 'Elements', 'Nodes', 'Max Nodes in Element', 'Area (km^2)']]
    for vpu in s.query(VectorProcessingUnit):
        rows.append(
            [vpu.name, len(vpu.catchment), vpu.get_node_count(), vpu.get_max_node_count(), vpu.get_area() * 1e-6])


if __name__ == '__main__':
    # setup_database()
    # fill_database()

    drop_create([Job, Timing])
    parse_job('/media/benkoziol/Extra Drive 1/yellowstone/logs/test-all-256-cores', 256)
