import numpy as np
from ocgis.interface.base.crs import CoordinateReferenceSystem
from ocgis.interface.base.dimension.spatial import SpatialGeometryPolygonDimension
from ocgis.util.geom_cabinet import GeomCabinetIterator
from shapely.geometry import MultiPolygon

from utools.analysis.shapefiles.db import metadata, Session, get_or_create, Shapefile, Catchment


def setup_database():
    metadata.create_all()


def analyze_shapefile(path, key, to_crs_epsg):
    s = Session()
    to_crs = CoordinateReferenceSystem(epsg=to_crs_epsg)
    shapefile = get_or_create(s, Shapefile, fullpath=path, key=key)
    gi = GeomCabinetIterator(path=path)
    for row in gi:
        geom = row['geom']
        if not geom.is_valid:
            geom = geom.buffer(0)
            assert geom.is_valid
        if isinstance(geom, MultiPolygon):
            itr = geom
            face_count = len(geom)
        else:
            itr = [geom]
            face_count = 1
        node_count = 0
        for element in itr:
            node_count += len(element.exterior.coords)
        catchment = Catchment(gridcode=row['properties']['GRIDCODE'],
                              node_count=node_count,
                              face_count=face_count,
                              shapefile=shapefile,
                              area=get_area(geom, to_crs))
        s.add(catchment)
    s.commit()
    s.close()


def get_area(geom, to_crs, from_crs=None):
    from_crs = from_crs or CoordinateReferenceSystem(epsg=4326)
    value = np.array([[0]], dtype=object)
    value[0, 0] = geom
    s = SpatialGeometryPolygonDimension(value=value)
    s.update_crs(to_crs, from_crs)
    return s.value[0, 0].area


if __name__ == '__main__':
    # setup_database()
    # path = '/home/benkoziol/Dropbox/NESII/project/pmesh/bin/NHDPlusTX/NHDPlus12/NHDPlusCatchment/Catchment.shp'
    # analyze_shapefile(path, 'NHDPlusTX-NHDPlus12', 3083)

    s = Session()
    shp = s.query(Shapefile).first()

    print shp.get_node_count()
    print shp.get_area() * 1e-6
    print shp.get_node_density()
    # stats = shp.get_stats()
    # for k, v in stats.iteritems():
    #     print '{0}\t{1}'.format(k, v)
    s.close()
