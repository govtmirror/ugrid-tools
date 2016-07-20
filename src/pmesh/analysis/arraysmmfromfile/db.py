import csv
import json

import numpy as np
from sqlalchemy import Float
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative.api import declarative_base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.schema import MetaData, Column
from sqlalchemy.types import Integer, String

connstr = 'sqlite://'
# connstr = 'postgresql://bkoziol:<password>@localhost/<database>'
# connstr = 'postgresql://{user}:{password}@{host}/{database}'
## four slashes for absolute paths - three for relative
# db_path = '/home/benkoziol/l/project/pmesh/src/pmesh/analysis/catchments.sqlite'
# connstr = 'sqlite:///{0}'.format(db_path)

engine = create_engine(connstr)
metadata = MetaData(bind=engine)
Base = declarative_base(metadata=metadata)
Session = sessionmaker(bind=engine)


class PrintOutput(Base):
    __tablename__ = 'output'
    uid = Column(Integer, primary_key=True)
    pet = Column(Integer, nullable=False)
    wtime = Column(Float, nullable=False)
    action = Column(String, nullable=False)
    message = Column(String, nullable=False)


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


def setup_database():
    metadata.create_all()


def dump_model_to_csv(Session, Model, path):
    s = Session()
    try:
        build = True
        with open(path, 'w') as f:
            writer = csv.writer(f)
            for row in s.query(Model):
                if build:
                    headers = [column.name for column in row.__table__.columns]
                    writer.writerow(headers)
                    build = False
                to_write = [getattr(row, header) for header in headers]
                writer.writerow(to_write)
    finally:
        s.close()


def fill_database():
    path = '/home/benkoziol/htmp/arraysmm-timing-20160512.out'
    setup_database()
    s = Session()
    with open(path) as f:
        lines = f.readlines()
        for l in lines:
            if 'json=' in l:
                jstring = l[6:]
                j = json.loads(jstring)
                o = PrintOutput(**j)
                s.add(o)
    s.commit()

    # array creation
    message = 'create source and destination arrays'
    start = s.query(PrintOutput).filter_by(action='start', message=message).all()
    stop = s.query(PrintOutput).filter_by(action='stop', message=message).all()
    v = []
    for e1, e2 in zip(start, stop):
        v.append(e2.wtime - e1.wtime)
    print(message)
    print(np.mean(v))

    # routehandle creation
    message = 'ESMF_ArraySMMStoreFromFile'
    start = s.query(PrintOutput).filter_by(action='start', message=message).all()
    stop = s.query(PrintOutput).filter_by(action='stop', message=message).all()
    v = []
    for e1, e2 in zip(start, stop):
        v.append(e2.wtime - e1.wtime)
    print(message)
    print(np.mean(v))

    # weight application
    message = 'ESMF_ArraySMM'
    start = s.query(PrintOutput).filter_by(action='start', message=message).all()
    stop = s.query(PrintOutput).filter_by(action='stop', message=message).all()
    v = []
    for e1, e2 in zip(start, stop):
        v.append(e2.wtime - e1.wtime)
    print(message)
    print(np.mean(v))

    # total time
    message = 'ApplySMMFromFile'
    start = s.query(PrintOutput).filter_by(action='start', message=message).all()
    stop = s.query(PrintOutput).filter_by(action='stop', message=message).all()
    v = []
    for e1, e2 in zip(start, stop):
        v.append(e2.wtime - e1.wtime)
    print(message)
    print(np.mean(v))


if __name__ == '__main__':
    fill_database()
