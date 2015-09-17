from ocgis.util.geom_cabinet import GeomCabinetIterator

SHP_PATH = '/home/benkoziol/htmp/nfie/FILED/catchment_singlepart_with_uid.shp'

g = GeomCabinetIterator(path=SHP_PATH, select_sql_where="GRIDCODE=1657788")

for ii in g:
    print len(ii['geom'].exterior.coords)