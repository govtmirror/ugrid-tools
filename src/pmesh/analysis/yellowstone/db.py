import re

from sqlalchemy import ForeignKey, Float
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative.api import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.schema import MetaData, Column
from sqlalchemy.types import Integer, String

connstr = 'sqlite://'
# connstr = 'postgresql://bkoziol:<password>@localhost/<database>'
# connstr = 'postgresql://{user}:{password}@{host}/{database}'
## four slashes for absolute paths - three for relative
# db_path = '/home/benkoziol/l/project/pmesh/src/pmesh/analysis/yellowstone/log_output.sqlite'
# connstr = 'sqlite:///{0}'.format(db_path)


engine = create_engine(connstr)
metadata = MetaData(bind=engine)
Base = declarative_base(metadata=metadata)
Session = sessionmaker(bind=engine)


class VectorProcessingUnit(Base):
    __tablename__ = 'vpu'
    vid = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    timing = relationship("Timing", backref=backref("vpu"))


class Job(Base):
    __tablename__ = 'job'
    jid = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    cpu_time = Column(Float, nullable=False)
    max_memory = Column(Float, nullable=False)
    average_memory = Column(Float, nullable=False)
    run_time = Column(Float, nullable=False)
    turnaround_time = Column(Float, nullable=False)

    @classmethod
    def create(cls, path):
        k = {}
        k['jid'] = re_file(path, 'Subject: Job (.+):').group(1)
        k['name'] = re_file(path, 'Job <(.+)> was submitted').group(1)
        k['cpu_time'] = re_file(path, 'CPU time : +(.+) sec').group(1)
        k['max_memory'] = re_file(path, 'Max Memory : +(.+) MB').group(1)
        k['average_memory'] = re_file(path, 'Average Memory : +(.+) MB').group(1)
        k['run_time'] = re_file(path, 'Run time : +(.+) sec').group(1)
        k['turnaround_time'] = re_file(path, 'Turnaround time : +(.+) sec').group(1)
        job = Job(**k)
        return job


class Timing(Base):
    __tablename__ = 'timing'
    tid = Column(Integer, primary_key=True)
    vid = Column(Integer, ForeignKey('vpu.vid'), nullable=False)
    apply_weights_start = Column(Float, nullable=False)
    apply_weights_stop = Column(Float, nullable=False)
    apply_weights_calculation_start = Column(Float, nullable=False)
    apply_weights_calculation_stop = Column(Float, nullable=False)
    create_weights = Column(Float, nullable=False)

    @classmethod
    def create(cls, path, vpu, create_weights):
        apply_weights_start = re_file(path, 'time=(.+)\): Starting weight application').group(1)
        apply_weights_stop = re_file(path, 'time=(.+)\): Finished weight application').group(1)
        apply_weights_calculation_start = re_file(path, 'time=(.+)\): Applying weights').group(1)
        apply_weights_calculation_stop = re_file(path, 'time=(.+)\): Writing output file').group(1)

        t = cls(vpu=vpu, apply_weights_start=apply_weights_start, apply_weights_stop=apply_weights_stop,
                apply_weights_calculation_start=apply_weights_calculation_start,
                apply_weights_calculation_stop=apply_weights_calculation_stop, create_weights=create_weights)
        return t

    @property
    def apply_weights(self):
        return self.apply_weights_stop - self.apply_weights_start

    @property
    def apply_weights_calculation(self):
        return self.apply_weights_calculation_stop - self.apply_weights_calculation_start


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


def re_file(path, pattern):
    with open(path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            search = re.search(pattern, line)
            if search is not None:
                return search


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
