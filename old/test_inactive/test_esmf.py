import ESMF
import numpy as np
import os
from ocgis import OcgOperations
from pyugrid.flexible_mesh.core import get_flexible_mesh
from pyugrid.flexible_mesh.helpers import GeometryManager
from shapely.geometry import MultiPolygon

from fmtools.regrid.core_esmpy import get_field_src
from fmtools.test.base import AbstractFMToolsTest


class Test(AbstractFMToolsTest):

    def test_disjoint_polygons(self):
        """Test mesh regridding with the source destination containing disjoint polygons."""

        ESMF.Manager(debug=True)
        self.set_debug(True)

        path_shp = os.path.join(self.path_bin, 'three_polygons', 'three_polygons.shp')
        path_out_nc = self.get_temporary_file_path('ugrid.nc')
        path_source_nc = self.get_temporary_file_path('source.nc')
        mesh_name = 'mesh'

        self.log.debug('creating source netcdf')
        row = np.linspace(-1, 1, 10)
        col = np.linspace(-1, 1, 10)
        self.create_source_netcdf_data(path_source_nc, row=row, col=col)
        ops = OcgOperations(dataset={'uri': path_source_nc}, output_format='shp', snippet=True, prefix='source_shp',
                            dir_output=self.path_current_tmp)
        ops.execute()

        self.log.debug('creating ugrid file: {}'.format(path_out_nc))
        gm = GeometryManager('SPECIAL', path=path_shp)
        geoms = [r['geom'] for r in gm.iter_records()]
        mp = MultiPolygon(geoms)
        # mp = box(-0.25, -0.25, 0.25, 0.25)

        records = [{'geom': mp, 'properties': {'UGID': 123}}]
        gm = GeometryManager('UGID', records=records, allow_multipart=True)
        fm = get_flexible_mesh(gm, mesh_name, False, False)
        fm.save_as_netcdf(path_out_nc, kwargs_dataset={'format': 'NETCDF3_CLASSIC'})

        self.log.debug('getting source field')
        srcgrid = ESMF.Grid(filename=path_source_nc, filetype=ESMF.FileFormat.GRIDSPEC,
                            coord_names=['longitude', 'latitude'], add_corner_stagger=True)
        srcfield = get_field_src(srcgrid, path_source_nc, 'pr')

        self.log.debug('getting destination grid')
        dstgrid = ESMF.Mesh(filename=path_out_nc, filetype=ESMF.FileFormat.UGRID, meshname=mesh_name)
        self.log.debug('getting destination field')
        dstfield = ESMF.Field(dstgrid, "dstfield", meshloc=ESMF.MeshLoc.ELEMENT, ndbounds=[srcfield.data.shape[0]])

        self.log.debug('creating regrid object')
        regrid = ESMF.Regrid(srcfield, dstfield, regrid_method=ESMF.RegridMethod.CONSERVE,
                             unmapped_action=ESMF.UnmappedAction.ERROR)
        # "zero_region" only weighted data will be touched.
        self.log.debug('executing regrid')
        dstfield = regrid(srcfield, dstfield, zero_region=ESMF.Region.SELECT)

        self.assertEqual(dstfield.data.shape, (366, 1))

        print dstfield.data

        self.log.debug('success')
