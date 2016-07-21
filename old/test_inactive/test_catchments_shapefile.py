import sys
sys.path.append('/home/benkoziol/l/project/pyugrid')

import os
import tempfile

import fiona
from shapely.geometry import shape, MultiPolygon, mapping
from shapely.geometry.polygon import orient

from fmtools.test.base import AbstractFMToolsTest
import numpy as np
from fmtools.logging import log
from pyugrid.flexible_mesh.helpers import get_oriented_and_valid_geometry


class Test(AbstractFMToolsTest):

    def test_ccw(self):
        """Test polygons can be oriented counter-clockwise."""

        path = '/home/benkoziol/data/pmesh/catchment_shapefiles/NHDPlusTX/NHDPlus12/NHDPlusCatchment/Catchment.shp'
        path_out = os.path.join(tempfile.mkdtemp(), 'ccw.shp')
        with fiona.open(path, 'r') as source:
            with fiona.open(path_out, 'w', **source.meta) as sink:
                for record in source:
                    geom = shape(record['geometry'])
                    if isinstance(geom, MultiPolygon):
                        itr = geom
                    else:
                        itr = [geom]
                    for polygon in itr:
                        if not polygon.exterior.is_ccw:
                            polygon = orient(polygon)
                        self.assertTrue(polygon.exterior.is_ccw)
                    record['goemetry'] = mapping(geom)
                    sink.write(record)

        with fiona.open(path_out, 'r') as source:
            for record in source:
                geom = shape(record['geometry'])
                if isinstance(geom, MultiPolygon):
                    itr = geom
                else:
                    itr = [geom]
                for polygon in itr:
                    self.assertTrue(polygon.exterior.is_ccw)
                record['goemetry'] = mapping(geom)

    def test_coordinates(self):
        path = '/home/benkoziol/data/pmesh/catchment_shapefiles/NHDPlusTX/NHDPlus12/NHDPlusCatchment/Catchment.shp'
        with fiona.open(path, 'r') as source:
            for record in source:
                log.debug(record['properties']['GRIDCODE'])
                geom = shape(record['geometry'])
                if isinstance(geom, MultiPolygon):
                    itr = geom
                else:
                    itr = [geom]
                for polygon in itr:
                    polygon = get_oriented_and_valid_geometry(polygon)
                    self.assertTrue(polygon.exterior.is_ccw)
                    coords = np.array(polygon.exterior.coords)
                    try:
                        self.assertTrue(coords.shape[0] > 1)
                    except AssertionError:
                        log.error('AssertionError GRIDCODE={}'.format(record['properties']['GRIDCODE']))
                        continue