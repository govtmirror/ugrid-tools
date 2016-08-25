import traceback
from ConfigParser import SafeConfigParser

from click.testing import CliRunner

from utools.test.base import AbstractUToolsTest
from utools_cli import convert


class Test(AbstractUToolsTest):
    def test_convert_with_file_geodatabase(self):
        self.handle_no_geodatabase()

        source_uid = 'GRIDCODE'
        source = self.path_nhd_seamless_file_geodatabase
        out_file = self.get_temporary_file_path('esmf_format.nc')
        feature_class = 'Catchment'
        config_path = self.get_temporary_file_path('config_path.cfg')
        dest_crs_wkt = 'PROJCS["Sphere_Lambert_Conformal_Conic",GEOGCS["WGS 84",DATUM["unknown",SPHEROID["WGS84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],PROJECTION["Lambert_Conformal_Conic_2SP"],PARAMETER["standard_parallel_1",30],PARAMETER["standard_parallel_2",60],PARAMETER["latitude_of_origin",40.0000076294],PARAMETER["central_meridian",-97],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["Meter",1]]'

        sp = SafeConfigParser()
        crs_section = 'National Water Model'
        crs_option = 'crs_wkt'
        sp.add_section(crs_section)
        sp.set(crs_section, crs_option, value=dest_crs_wkt)
        with open(config_path, 'w') as fp:
            sp.write(fp)

        runner = CliRunner()
        cli_args = ['-e', out_file, '-u', source_uid, "-s", source, '--debug', '--feature-class', feature_class,
                    '--config-path', config_path, '--dest_crs_index', 'National Water Model,crs_wkt']
        result = runner.invoke(convert, cli_args)
        try:
            self.assertEqual(result.exit_code, 0)
        except AssertionError:
            print result.exit_code
            print result.output
            traceback.print_exception(*result.exc_info)
            raise result.exception
        else:
            with self.nc_scope(out_file) as actual:
                self.assertEqual(actual.variables['GRIDCODE'].shape, (1,))

                # Test coordinates are no longer spherical lat/lon, but have a converted coordinate system.
                actual_coords = actual.variables['nodeCoords'][:]
                self.assertGreater(actual_coords.mean(), 360.)
