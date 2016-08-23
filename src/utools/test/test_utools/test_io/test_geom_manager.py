import os

from osgeo import osr
from shapely.geometry import MultiPolygon
from shapely.geometry import Polygon

from utools.io.core import get_flexible_mesh
from utools.io.geom_manager import GeometryManager
from utools.io.helpers import convert_collection_to_esmf_format
from utools.test.base import AbstractUToolsTest, attr


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

    @attr('dev')
    def test_system_convert_file_geodatabase_to_esmf_format(self):
        """This is a development test because it requires a file geodatabase SDK driver to write. ESRI proprietary."""

        path = '/media/benkoziol/Extra Drive 1/data/nfie/NHDPlusNationalData/NHDPlusV21_National_Seamless.gdb'
        driver_kwargs = {'feature_class': 'Catchment'}
        dest_crs_wkt = 'PROJCS["Sphere_Lambert_Conformal_Conic",GEOGCS["WGS 84",DATUM["unknown",SPHEROID["WGS84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],PROJECTION["Lambert_Conformal_Conic_2SP"],PARAMETER["standard_parallel_1",30],PARAMETER["standard_parallel_2",60],PARAMETER["latitude_of_origin",40.0000076294],PARAMETER["central_meridian",-97],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["Meter",1]]'
        sr = osr.SpatialReference()
        sr.ImportFromWkt(dest_crs_wkt)
        out_path = self.get_temporary_file_path('out.nc')

        gm = GeometryManager('GRIDCODE', path=path, allow_multipart=True, node_threshold=5000,
                             driver_kwargs=driver_kwargs, slc=[10, 110])
        coll = get_flexible_mesh(gm, '', True, with_connectivity=False)
        with self.nc_scope(out_path, 'w') as ds:
            convert_collection_to_esmf_format(coll, ds, polygon_break_value=-8, face_uid_name='GRIDCODE')

    @attr('dev')
    def test_system_read_file_geodatabase(self):
        """This is a development test because it requires a file geodatabase SDK driver to write. ESRI proprietary."""

        path = '/media/benkoziol/Extra Drive 1/data/nfie/NHDPlusNationalData/NHDPlusV21_National_Seamless.gdb'
        driver_kwargs = {'feature_class': 'Catchment'}
        dest_crs_wkt = 'PROJCS["Sphere_Lambert_Conformal_Conic",GEOGCS["WGS 84",DATUM["unknown",SPHEROID["WGS84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],PROJECTION["Lambert_Conformal_Conic_2SP"],PARAMETER["standard_parallel_1",30],PARAMETER["standard_parallel_2",60],PARAMETER["latitude_of_origin",40.0000076294],PARAMETER["central_meridian",-97],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["Meter",1]]'
        sr = osr.SpatialReference()
        sr.ImportFromWkt(dest_crs_wkt)

        gm = GeometryManager('GRIDCODE', path=path, allow_multipart=True, driver_kwargs=driver_kwargs)
        for ctr, row in enumerate(gm.iter_records(dest_crs=sr)):
            if ctr > 10:
                break
            self.assertIsInstance(row['geom'], (Polygon, MultiPolygon))
