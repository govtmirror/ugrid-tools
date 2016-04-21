from collections import OrderedDict

import numpy as np
from sqlalchemy import ForeignKey, Float
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative.api import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.schema import MetaData, Column
from sqlalchemy.types import Integer, String

# connstr = 'sqlite://'
# connstr = 'postgresql://bkoziol:<password>@localhost/<database>'
# connstr = 'postgresql://{user}:{password}@{host}/{database}'
## four slashes for absolute paths - three for relative
db_path = '/home/benkoziol/l/project/pmesh/src/analysis/nodes.sqlite'
connstr = 'sqlite:///{0}'.format(db_path)

engine = create_engine(connstr)
metadata = MetaData(bind=engine)
Base = declarative_base(metadata=metadata)
Session = sessionmaker(bind=engine)


class Shapefile(Base):
    __tablename__ = 'shapefile'
    sid = Column(Integer, primary_key=True)
    fullpath = Column(String, unique=True, nullable=False)
    key = Column(String, nullable=False)
    catchment = relationship("Catchment", backref=backref("shapefile", uselist=False))

    def get_area(self):
        """
        :returns: Area in square meters.
        :rtype: float
        """

        return reduce(lambda x, y: x + y, (c.area for c in self.catchment))

    def get_node_count(self):
        return reduce(lambda x, y: x + y, (c.node_count for c in self.catchment))

    def get_node_density(self):
        """
        :returns: Node density in node count per square kilometer.
        :rtype: float
        """

        node_count = self.get_node_count()
        area_sq_km = self.get_area() * 1e-6
        return node_count / area_sq_km

    def get_stats(self):
        ret = OrderedDict()
        catchment = self.catchment
        node_counts = np.array([c.node_count for c in catchment])
        face_counts = np.array([c.face_count for c in catchment])

        ret['nMesh2_face'] = face_counts.sum()
        ret['nMesh2_node'] = node_counts.sum()
        ret['nMesh2_edge'] = ret['nMesh2_node'] - node_counts.shape[0]
        ret['nMaxMesh2_face_nodes'] = node_counts.max()

        return ret


class Catchment(Base):
    __tablename__ = 'catchment'
    gridcode = Column(Integer, primary_key=True)
    sid = Column(Integer, ForeignKey('shapefile.sid'), nullable=False)
    node_count = Column(Integer, nullable=False)
    face_count = Column(Integer, nullable=False)
    # Area is in square meters.
    area = Column(Float, nullable=False)


def get_or_create(session, Model, **kwargs):
    try:
        obj = session.query(Model).filter_by(**kwargs).one()
    except NoResultFound:
        obj = Model(**kwargs)
        session.add(obj)
        session.commit()
    return obj


def drop_create(models, drop=True):
    if type(models) not in [list, tuple]:
        models = [models]
    if drop:
        for model in models:
            model.__table__.drop(checkfirst=True)
    models.reverse()
    for model in models:
        model.__table__.create()

# def dump_model_to_csv(Session,Model,path):
#     s = Session()
#     try:
#         build = True
#         with open(path,'w') as f:
#             writer = csv.writer(f)
#             for row in s.query(Model):
#                 if build:
#                     headers = [column.name for column in row.__table__.columns]
#                     writer.writerow(headers)
#                     build = False
#                 to_write = [getattr(row,header) for header in headers]
#                 writer.writerow(to_write)
#     finally:
#         s.close()
