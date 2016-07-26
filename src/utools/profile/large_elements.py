"""Profiling for large, complex elements."""
import re
import time
from os import listdir
from os.path import join

import fiona
import logbook
from joblib import Parallel, delayed
from sqlalchemy import func

from utools.analysis.db import Session, VectorProcessingUnit, Catchment
from utools.logging import log, log_entry_exit
from utools.prep.prep_shapefiles import convert_to_esmf_format
from utools.regrid.core_esmf import create_weights_file

SHAPEFILE_DIR = '/home/benkoziol/l/data/nfie/linked_catchment_shapefiles'
WD = '/home/ubuntu/storage/pmesh_profiling'
PATH_SOURCE_DATA = '/home/ubuntu/storage/exact_data/exact-conus-025degree_20160316-1737.nc'
# PATH_SOURCE_DATA = '/home/benkoziol/l/data/nfie/storage/exact_data/exact-conus-025degree_20160316-1737.nc'
ESMF_EXE_PATH = '/home/ubuntu/miniconda2/envs/nfie/bin/ESMF_RegridWeightGen'
# ESMF_EXE_PATH = '/home/benkoziol/anaconda2/envs/pmesh/bin/ESMF_RegridWeightGen'
ESMF_WEIGHTS_OUTPUT_DIR = '/home/ubuntu/storage/scratch'


@log_entry_exit
def make_shapefiles_and_esmf_format():
    log.level = logbook.DEBUG

    template_shapefile = 'single_element_{gridcode}_{node_count}.shp'
    template_esmf_format = 'esmf_single_element_{gridcode}_{node_count}.nc'

    to_process = get_representative_nodes()

    for tp in to_process:
        log.debug(tp)
        gridcode = tp['gridcode']
        node_count = tp['node_count']
        filename_shapefile = template_shapefile.format(gridcode=gridcode, node_count=node_count)
        filename_esmf_format = template_esmf_format.format(gridcode=gridcode, node_count=node_count)

        # Extract the element and write the shapefile.
        sink_path = join(WD, filename_shapefile)
        source_path = get_source_shapefile(SHAPEFILE_DIR, tp['name'])
        log.debug(source_path)
        found = False
        with fiona.open(source_path) as source:
            with fiona.open(sink_path, 'w', **source.meta) as sink:
                for record in source:
                    if record['properties']['GRIDCODE'] == gridcode:
                        found = True
                        sink.write(record)
                        break
        assert found

        # Convert the shapefile to ESMF format.
        path_out_nc = join(WD, filename_esmf_format)
        path_in_shp = sink_path
        convert_to_esmf_format(path_out_nc, path_in_shp, 'GRIDCODE')


def make_weight_files():
    n_jobs = 16
    to_process = []

    log.level = logbook.INFO

    for ctr, l in enumerate(listdir(WD)):
        # if ctr > 20: break

        if l.endswith('.nc'):
            path_out_weights_nc = join(ESMF_WEIGHTS_OUTPUT_DIR, 'weights_' + l)
            esmf_format = join(WD, l)

            log.debug(path_out_weights_nc)
            log.debug(esmf_format)

            search = re.search('esmf_single_element_(.+)_(.+).nc', l)
            gridcode, node_count = search.group(1), search.group(2)
            kwds = {'esmf_format': esmf_format,
                    'path_out_weights_nc': path_out_weights_nc,
                    'gridcode': int(gridcode),
                    'node_count': int(node_count)}
            to_process.append(kwds)

            log.debug(kwds)

    rtimes = Parallel(n_jobs=n_jobs)(delayed(make_weight_file)(**k) for k in to_process)

    for idx, k in enumerate(to_process):
        k['time'] = rtimes[idx]

    log.info(to_process)


def make_weight_file(**kwargs):
    esmf_format = kwargs['esmf_format']
    path_out_weights_nc = kwargs['path_out_weights_nc']
    gridcode = kwargs['gridcode']
    node_count = kwargs['node_count']

    log.info('Starting weight generation: {}, (gridcode={}, node_count={})'.format(esmf_format, gridcode, node_count))
    t1 = time.time()
    create_weights_file(None, ESMF_EXE_PATH, PATH_SOURCE_DATA, esmf_format, path_out_weights_nc)
    t2 = time.time()
    log.info('Finished weight generation: {}, (gridcode={}, node_count={})'.format(esmf_format, gridcode, node_count))
    return t2 - t1


def get_source_shapefile(search_dir, name):
    ret = None
    for l in listdir(search_dir):
        if l.endswith('shp') and str(name) in l:
            ret = join(search_dir, l)
    assert ret is not None
    return ret


def get_source_esmf_mesh_file(gridcode):
    for l in listdir(WD):
        if l.startswith('esmf_') and str(gridcode) in l:
            return join(WD, l)


def plot_timing_results():
    from timing_data import data
    from matplotlib import pyplot as plt

    x = [ii['node_count'] for ii in data]
    y = [ii['time'] / 60. for ii in data]

    # sort_idx = np.argsort(x)
    # print sort_idx
    # x = x[sort_idx]
    # print x
    # thh

    # plt.plot(x, y)
    plt.plot(x, y, 'ro')
    plt.xlabel('Node Count')
    plt.ylabel('Processing Time (Minutes)')
    plt.grid(True)
    plt.title('Processing Times for Mesh Element Node Counts')

    plt.show()

    # fig = plt.figure(figsize=(8, 6))
    # ax = fig.add_subplot(111)
    # plt.plot(arr[:, 0], arr[:, 1])
    # plt.plot(arr[:, 0], arr[:, 1], 'ro')
    # for ctr, xy in enumerate(zip(arr[:, 0].flat, arr[:, 1].flat)):
    #     xy = list(xy)
    #     xy[0] += 0.00001
    #     xy[1] += 0.00001
    #     ax.annotate(str(ctr), xy=xy)
    # plt.savefig('/home/benkoziol/htmp/pmesh/element images/element-69.png', dpi=300)
    # plt.show()


def get_max_nodes():
    """
    :return: The maximum number of nodes in an element across catchments.
    :rtype: int
    """

    s = Session()
    q = s.query(func.max(Catchment.node_count))
    max_nodes = q.one()[0]
    s.close()
    return max_nodes


def get_representative_nodes():
    """Get elements with a reasonable distribution of node counts."""

    step = 1000
    start = 0
    stop = 60000
    limit = 50
    record_names = ['name', 'gridcode', 'node_count']

    ranges = []
    to_process = []

    s = Session()

    while start < stop:
        ranges.append([start, start + step])
        start += step

    for ctr, select_range in enumerate(ranges):
        log.debug(select_range)
        q = s.query(VectorProcessingUnit.name, Catchment.gridcode, Catchment.node_count).join(Catchment)
        q = q.filter(Catchment.node_count >= select_range[0]).filter(Catchment.node_count < select_range[1])
        q = q.order_by(func.random()).limit(limit)

        for idx, record in enumerate(q):
            to_process.append(dict(zip(record_names, record)))

    s.close()

    return to_process


if __name__ == '__main__':
    # make_shapefiles_and_esmf_format()
    # make_weight_files()
    plot_timing_results()
    # get_representative_nodes()
