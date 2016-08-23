import os
from copy import copy

from osgeo import ogr, osr
from shapely.geometry import shape
from shapely.geometry.base import BaseMultipartGeometry

from utools.io.geom_cabinet import GeomCabinetIterator, GeomCabinet
from utools.io.helpers import get_node_count, get_split_polygon_by_node_threshold

ogr.UseExceptions()
osr.UseExceptions()


class GeometryManager(object):
    """
    Provides iteration, validation, and other management routines for collecting vector geometries from record lists or
    flat files.
    """

    def __init__(self, name_uid, path=None, records=None, path_rtree=None, allow_multipart=False, node_threshold=None,
                 dest_crs=None, driver_kwargs=None, slc=None):
        if path_rtree is not None:
            assert os.path.exists(path_rtree + '.idx')

        self.path = path
        self.path_rtree = path_rtree
        self.name_uid = name_uid
        self.records = copy(records)
        self.allow_multipart = allow_multipart
        self.node_threshold = node_threshold
        self.dest_crs = dest_crs
        self.driver_kwargs = driver_kwargs
        self.slc = slc

        self._has_provided_records = False if records is None else True

    def __len__(self):
        if self.records is None:
            ret = len(GeomCabinetIterator(path=self.path, driver_kwargs=self.driver_kwargs, slc=self.slc))
        else:
            ret = len(self.records)
        return ret

    @property
    def meta(self):
        return GeomCabinet(path=self.path).get_meta(path=self.path)

    def get_spatial_index(self):
        from spatial_index import SpatialIndex

        si = SpatialIndex(path=self.path_rtree)
        # Only add new records to the index if we are working in-memory.
        if self.path_rtree is None:
            for uid, record in self.iter_records(return_uid=True):
                si.add(uid, record['geom'])
        return si

    def iter_records(self, return_uid=False, select_uid=None, slc=None, dest_crs=None):
        # Use records attached to the object or load records from source data.
        to_iter = self.records or self._get_records_(select_uid=select_uid, slc=slc, dest_crs=dest_crs)

        if self.records is not None and slc is not None:
            to_iter = to_iter[slc[0]:slc[1]]

        for ctr, record in enumerate(to_iter):
            if self._has_provided_records and 'geom' not in record:
                record['geom'] = shape(record['geometry'])
                # Only use the geometry objects from here. Maintaining the list of coordinates is superfluous.
                record.pop('geometry')
            self._validate_record_(record)

            # Modify the geometry if a node threshold is provided. This breaks the polygon object into pieces with the
            # approximate node count.
            if self.node_threshold is not None and get_node_count(record['geom']) > self.node_threshold:
                record['geom'] = get_split_polygon_by_node_threshold(record['geom'], self.node_threshold)

            if return_uid:
                uid = record['properties'][self.name_uid]
                yld = (uid, record)
            else:
                yld = record
            yield yld

    def _get_records_(self, select_uid=None, slc=None, dest_crs=None):
        slc = slc or self.slc
        gi = GeomCabinetIterator(path=self.path, uid=self.name_uid, select_uid=select_uid, slc=slc, dest_crs=dest_crs,
                                 driver_kwargs=self.driver_kwargs)
        return gi

    def _validate_record_(self, record):
        geom = record['geom']

        # This should happen before any buffering. The buffering check may result in a single polygon object.
        if not self.allow_multipart and isinstance(geom, BaseMultipartGeometry):
            msg = 'Only singlepart geometries allowed. Perhaps "utools.convert_multipart_to_singlepart" would be ' \
                  'useful?'
            raise ValueError(msg)
