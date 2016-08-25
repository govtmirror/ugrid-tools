import os

import ocgis

# ESMF.Manager(debug=True)

WRF_GRID_PATH = '/media/benkoziol/Extra Drive 1/data/nfie/NWM_IOC_1km_grid_to_Ben.nc'
TEST_CARTESIAN_FILENAME = os.path.expanduser('~/htmp/test_cartesian_grid_20160525.nc')

# grid = ESMF.Grid(filename=WRF_GRID_PATH, filetype=FileFormat.GRIDSPEC, coord_names=['x', 'y'], coord_sys=CoordSys.CART,
#                  is_sphere=

rd = ocgis.RequestDataset(WRF_GRID_PATH)
vc = rd.get_variable_collection()[{'x': slice(0, 10), 'y': slice(0, 20)}]

coords_vars = ['x', 'y']
for c in coords_vars:
    var = vc[c]
    # print c, var.extent
    var.set_extrapolated_bounds('{}_bounds'.format(c), 'bounds')
    # print var.attrs
for var in vc.values():
    var.attrs.pop('esri_pe_string', None)
    var.attrs.pop('spatial_ref', None)
    var.attrs.pop('GeoTransform', None)

vc.write(TEST_CARTESIAN_FILENAME)

# print vc.shapes

import ipdb;

ipdb.set_trace()
