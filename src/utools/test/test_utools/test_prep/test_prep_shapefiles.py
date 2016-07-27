import os
from unittest import SkipTest

import fiona
import numpy as np
from ocgis.api.request.base import RequestDataset
from ocgis.api.request.driver.vector import DriverVector
from shapely import wkt
from shapely.geometry import shape

from utools.helpers import write_fiona
from utools.io.helpers import get_split_polygon_by_node_threshold
from utools.io.mpi import MPI_RANK, MPI_COMM
from utools.prep.prep_shapefiles import convert_to_esmf_format
from utools.test import long_lines
from utools.test.base import AbstractUToolsTest, attr


class Test(AbstractUToolsTest):
    @property
    def path_in_shp(self):
        return os.path.join(self.path_bin, 'nhd_catchments_texas', 'nhd_catchments_texas.shp')

    @attr('mpi')
    def test_convert_to_esmf_format(self):
        name_uid = 'GRIDCODE'
        path_out_nc = self.get_temporary_file_path('out.nc')
        convert_to_esmf_format(path_out_nc, self.path_in_shp, name_uid)

        if MPI_RANK == 0:
            with self.nc_scope(path_out_nc) as ds:
                self.assertEqual(len(ds.variables), 6)

        MPI_COMM.Barrier()

    @attr('mpi')
    def test_convert_to_esmf_format_node_threshold(self):
        """Test conversion with a node threshold for the elements."""
        name_uid = 'GRIDCODE'
        path_out_nc = self.get_temporary_file_path('out.nc')
        convert_to_esmf_format(path_out_nc, self.path_in_shp, name_uid, node_threshold=80)

        if MPI_RANK == 0:
            with self.nc_scope(path_out_nc) as ds:
                self.assertGreater(ds.dimensions['nodeCount'], 16867)
                self.assertEqual(len(ds.variables), 6)

        MPI_COMM.Barrier()

    def test_get_split_polygon_by_node_threshold(self):
        mp = long_lines.mp
        geom = wkt.loads(mp)

        # write_fiona(geom, '01-original_geom')
        actual = get_split_polygon_by_node_threshold(geom, 10)
        # write_fiona(actual, '01-assembled')
        self.assertAlmostEqual(geom.area, actual.area)

    def test_dev_get_split_polygon_by_node_threshold_many_nodes(self):
        raise SkipTest('development only')
        self.set_debug()

        shp_path = '/home/benkoziol/l/data/nfie/linked_catchment_shapefiles/linked_13-RioGrande.shp'

        with fiona.open(shp_path) as source:
            for record in source:
                if record['properties']['GRIDCODE'] == 2674572:
                    geom = shape(record['geometry'])

        # write_fiona(geom, '01-original_geom')
        actual = get_split_polygon_by_node_threshold(geom, 10000)
        # write_fiona(actual, '01-assembled')
        self.assertAlmostEqual(geom.area, actual.area)

        for p in actual:
            print len(p.exterior.coords)

        write_fiona(actual, 'assembled')

    def test_dev_get_split_shapefile(self):
        raise SkipTest('development only')
        self.set_debug()

        shp_path = '/home/benkoziol/l/data/nfie/linked_catchment_shapefiles/linked_13-RioGrande.shp'
        rd = RequestDataset(uri=shp_path)
        field = rd.get()
        self.log.debug('loading from file')
        field.geom.value
        node_count = map(get_node_count, field.geom.value)
        select = np.array(node_count) > 10000
        to_split = field['GRIDCODE'][select]
        for gc in to_split.value.flat:
            self.log.debug('target gridcode: {}'.format(gc))
            idx = np.where(field['GRIDCODE'].value == gc)[0][0]
            target_geom = field.geom.value[idx]
            split_geom = get_split_polygon_by_node_threshold(target_geom, 10000)
            # write_fiona(split_geom, gc)
            self.assertAlmostEqual(split_geom.area, target_geom.area)
            field.geom.value[idx] = split_geom
            self.assertAlmostEqual(field.geom.value[idx].area, target_geom.area)
        self.log.debug(field.geom.geom_type)
        # field.geom[select].parent.write('/tmp/rio-grande-assembled.shp', driver=DriverVector)

        # write_fiona(field.geom.value, 'rio-grande-assembled')
        self.log.debug('writing shapefile')
        field.write('/tmp/rio-grande-assembled.shp', driver=DriverVector)
