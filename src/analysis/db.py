from collections import OrderedDict
from sqlalchemy import ForeignKey
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.schema import MetaData, Column
from sqlalchemy.ext.declarative.api import declarative_base
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.types import Integer, String
import numpy as np
import pylab


# connstr = 'sqlite://'
#connstr = 'postgresql://bkoziol:<password>@localhost/<database>'
#connstr = 'postgresql://{user}:{password}@{host}/{database}'
## four slashes for absolute paths - three for relative
db_path = '/home/benkoziol/l/project/nfie/src/analysis/nodes.sqlite'
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

    def get_stats(self):
        ret = OrderedDict()
        catchment = self.catchment
        node_counts = np.array([c.node_count for c in catchment])
        face_counts = np.array([c.face_count for c in catchment])

        # sorted = np.sort(node_counts)
        # print sorted[-int(0.05*node_counts.shape[0]):]
        # print sorted[-int(10):]

        ret['nMesh2_face'] = face_counts.sum()
        ret['nMesh2_node'] = node_counts.sum()
        ret['nMesh2_edge'] = ret['nMesh2_node']
        ret['nMaxMesh2_face_nodes'] = node_counts.max()
        # ret['Mean Node Count per Face'] = node_counts.mean()
        # ret['Median Node Count per Face'] = np.median(node_counts)
        # ret['Min Number of Nodes in a Face'] = node_counts.min()
        # ret['Max Number of Component Elements in a Face'] = face_counts.max()
        # ret['Mean Number of Component Elements in a Face'] = face_counts.mean()
        # ret['Median Number of Component Elements in a Face'] = np.median(face_counts)
        # ret['Total Faces Composed of Multiple Elements'] = np.sum(face_counts > 1)
        # ret['Total Node ']

        return ret


class Catchment(Base):
    __tablename__ = 'catchment'
    gridcode = Column(Integer, primary_key=True)
    sid = Column(Integer, ForeignKey('shapefile.sid'), nullable=False)
    node_count = Column(Integer, nullable=False)
    face_count = Column(Integer, nullable=False)


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


#
#
# class Geography(UserDefinedType):
#
#     def get_col_spec(self):
#         return('geography')
#
# class NotNullColumn(Column):
#
#     def __init__(self,*args,**kwds):
#         kwds.update({'nullable':False})
#         super(NotNullColumn,self).__init__(*args,**kwds)
#
#
# class SqlBase(object):
#     id = Column(Integer,primary_key=True)
#
#     @declared_attr
#     def __tablename__(cls):
#         return cls.__name__.lower()
#
# ## LOADER CLASS ----------------------------------------------------------------
#
# class SqlTable(object):
#     Model = None
#     Models = []
#     create = True
#     drop = True
#
#     def __init__(self):
#         assert(self.Model)
#         self.Models = self.Models or [self.Model]
#
#     def drop_create(self):
#         _Models = copy.copy(self.Models)
#         if self.drop:
#             for Model in _Models:
#                 Model.__table__.drop(checkfirst=True)
#         _Models.reverse()
#         for Model in _Models:
#             Model.__table__.create()
#
#     def load(self,drop_create=True):
#         if self.create:
#             self.drop_create()
#         self._load_()
#
#     def _load_(self):
#         raise(NotImplementedError)
#
#     @staticmethod
#     def get_setattr(attrs,target,origin):
#         for attr in attrs:
#             setattr(target,attr,getattr(origin,attr))
#
#
# ## SELECT INTO -----------------------------------------------------------------
#
# from sqlalchemy import *
# from sqlalchemy.sql.expression import Executable, ClauseElement
# from sqlalchemy.ext import compiler
#
#
# class SelectInto(Executable, ClauseElement):
#     def __init__(self, select, table_name):
#         self.select = select
#         self.table_name = table_name
#
#
# @compiler.compiles(SelectInto)
# def compile(element, compiler, **kw):
#     return "%s INTO '%s'" % (
#         compiler.process(element.select), element.table_name
#     )
#
#
# e = SelectInto(select([s.dim_date_table]).where(s.dim_date_table.c.Year==2009), 'tmp_table')
# print e
# eng.execute(e)
#
# ## -----------------------------------------------------------------------------
#
# class Raster(types.UserDefinedType):
#     pass
#
# class Geometry(types.UserDefinedType):
#     pass
#
# class set_return(ColumnElement):
#     def __init__(self,base,field):
#         self.base = base
#         self.field = field
#         self.type = None # throws an error unless declared...
#
# @compiles(set_return)
# def compile(expr, compiler, **kw):
#     return '(' + compiler.process(expr.base) + ').' + expr.field
# #
# #def debug_inline_params(stmt, bind=None):
# #    """Compiles a query or a statement and inlines bindparams.
# #
# #    WARNING: Does not do any escaping."""
# #    if isinstance(stmt, sqlalchemy.orm.Query):
# #        if bind is None:
# #            bind = stmt.session.get_bind(stmt._mapper_zero_or_none())
# #        stmt = stmt.statement
# #    else:
# #        if bind is None:
# #            bind = stmt.bind
# #
# #    compiler = bind.dialect.statement_compiler(bind.dialect, stmt)
# #    compiler.bindtemplate = "%%(%(name)s)s"
# #    compiler.compile()
# #    return compiler.string % dict((k,repr(v)) for k,v in compiler.params.items())
#
# ## -----------------------------------------------------------------------------
#
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