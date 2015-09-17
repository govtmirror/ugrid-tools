import os
from ocgis.util.geom_cabinet import GeomCabinetIterator
from shapely.geometry import MultiPolygon
from analysis.db import metadata, Session, get_or_create, Shapefile, Catchment


def setup_database():
    metadata.create_all()


def analyze_shapefile(path, key):
    s = Session()
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
                              shapefile=shapefile)
        s.add(catchment)
    s.commit()
    s.close()


if __name__ == '__main__':
    # setup_database()
    # path = '/home/benkoziol/Dropbox/NESII/project/nfie/bin/NHDPlusTX/NHDPlus12/NHDPlusCatchment/Catchment.shp'
    # analyze_shapefile(path, 'NHDPlusTX-NHDPlus12')

    s = Session()
    shp = s.query(Shapefile).first()
    stats = shp.get_stats()
    for k, v in stats.iteritems():
        print '{0}\t{1}'.format(k, v)
    s.close()
