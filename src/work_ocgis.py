import tempfile
import ocgis
from ocgis.util.geom_cabinet import GeomCabinetIterator
from dispatch import MPI_SIZE, MPI_RANK, MPI_COMM_WORLD
from work import PATH_CATCHMENT_SHP, PATH_CLIMATE_DATA, PATH_SINGLEPART_SHAPEFILE, PATH_FAKE_DATA
import numpy as np
from work import log


def area_weighted():
    in_shp = PATH_CATCHMENT_SHP
    # in_shp = PATH_SINGLEPART_SHAPEFILE
    # in_data = PATH_CLIMATE_DATA
    in_data = PATH_FAKE_DATA
    ocgis.env.VERBOSE = False
    geom_uid = 'GRIDCODE'

    # if MPI_RANK == 0:
    log.info('starting')
    gi = GeomCabinetIterator(path=in_shp)
        # uids = [e['properties'][geom_uid] for e in gi]
        # uids.sort()
        # split = np.array_split(uids, MPI_SIZE)
    # else:
    #     split = None

    # split = MPI_COMM_WORLD.scatter(split, root=0)

    ops = ocgis.OcgOperations(dataset={'uri': in_data},
                              geom=gi,
                              # geom_select_uid=split.tolist(),
                              # output_format='shp',
                              aggregate=True,
                              spatial_operation='clip',
                              # snippet=True,
                              dir_output=tempfile.mkdtemp())
    ret = ops.execute()

    new_ret = {}
    for uid, fdict in ret.iteritems():
        new_ret[uid] = fdict.values()[0].variables.first().value.data

    log.info('finished main (rank={0}'.format(MPI_RANK))

    new_ret = MPI_COMM_WORLD.gather(new_ret, root=0)

    if MPI_RANK == 0:
        fret = {}
        for e in new_ret:
            fret.update(e)

        log.info('success')

if __name__ == '__main__':
    area_weighted()