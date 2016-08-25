import ESMF
from ESMF.api.constants import FileFormat, CoordSys

ESMF.Manager(debug=True)

WRF_GRID_PATH = '/media/benkoziol/Extra Drive 1/data/nfie/NWM_IOC_1km_grid_to_Ben.nc'

grid = ESMF.Grid(filename=WRF_GRID_PATH, filetype=FileFormat.GRIDSPEC, coord_names=['x', 'y'], coord_sys=CoordSys.CART,
                 is_sphere=False)
import ipdb;

ipdb.set_trace()
