import os

from osgeo import osr

from utools.io.geom_manager import GeometryManager
from utools.test.base import AbstractUToolsTest


class TestGeomManager(AbstractUToolsTest):
    @property
    def path_nhd_catchments_texas(self):
        return os.path.join(self.path_bin, 'nhd_catchments_texas', 'nhd_catchments_texas.shp')

    def test_system_converting_coordinate_system(self):
        dest_crs_wkt = 'PROJCS["Sphere_Lambert_Conformal_Conic",GEOGCS["WGS 84",DATUM["unknown",SPHEROID["WGS84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],PROJECTION["Lambert_Conformal_Conic_2SP"],PARAMETER["standard_parallel_1",30],PARAMETER["standard_parallel_2",60],PARAMETER["latitude_of_origin",40.0000076294],PARAMETER["central_meridian",-97],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["Meter",1]]'
        sr = osr.SpatialReference()
        sr.ImportFromWkt(dest_crs_wkt)
        gm = GeometryManager('GRIDCODE', path=self.path_nhd_catchments_texas, allow_multipart=True)
        for row_orig, row_transform in zip(gm.iter_records(dest_crs=sr), gm.iter_records()):
            self.assertNotEqual(row_orig['geom'].bounds, row_transform['geom'].bounds)
