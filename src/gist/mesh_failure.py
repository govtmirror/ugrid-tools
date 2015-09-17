import ESMF


# Data available at: https://www.dropbox.com/s/dmsexup1kshfav0/data-mesh_failure.zip?dl=0
PATH_SOURCE_DATA = 'fake_data.nc'
PATH_UGRID_FILE = 'catchments.nc'


ESMF.Manager(debug=True)

print('getting source field')
grid = ESMF.Grid(filename=PATH_SOURCE_DATA, filetype=ESMF.FileFormat.GRIDSPEC)
srcfield = ESMF.Field(grid, staggerloc=ESMF.StaggerLoc.CENTER)
srcfield.read(filename=PATH_SOURCE_DATA, variable="pr")

print('getting destination mesh')
dstgrid = ESMF.Mesh(filename=PATH_UGRID_FILE, filetype=ESMF.FileFormat.UGRID, meshname="Mesh2")
print('getting destination field')
dstfield = ESMF.Field(dstgrid, "dstfield", meshloc=ESMF.MeshLoc.ELEMENT, ndbounds=[366])

print('creating regrid object')
# Fails for both CONSERVE and BILINEAR with same exit code and message.
regrid = ESMF.Regrid(srcfield, dstfield, regrid_method=ESMF.RegridMethod.CONSERVE,
                     unmapped_action=ESMF.UnmappedAction.IGNORE)
print('executing regrid')
dstfield = regrid(srcfield, dstfield)
