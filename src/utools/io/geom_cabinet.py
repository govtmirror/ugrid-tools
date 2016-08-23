import os
from collections import OrderedDict
from copy import deepcopy

import fiona
import ogr
from shapely import wkb


class GeomCabinet(object):
    """
    Access vector GIS files stored in a common location.

    :param path: Absolute path the directory holding shapefile folders.
    :type path: str
    """

    def __init__(self, path=None):
        self.path = path

    def keys(self):
        """Return a list of the shapefile keys contained in the search directory.

        :rtype: list of str
        """
        ret = []
        for dirpath, dirnames, filenames in os.walk(self.path):
            for fn in filenames:
                if fn.endswith('shp'):
                    ret.append(os.path.splitext(fn)[0])
        return ret

    def get_meta(self, key=None, path=None):
        path = path or self.get_shp_path(key)
        with fiona.open(path, 'r') as source:
            return source.meta

    def get_shp_path(self, key):
        return self._get_path_(key, ext='shp')

    def get_cfg_path(self, key):
        return self._get_path_(key, ext='cfg')

    def _get_path_(self, key, ext='shp'):
        ret = None
        for dirpath, dirnames, filenames in os.walk(self.path):
            for filename in filenames:
                if filename.endswith(ext) and os.path.splitext(filename)[0] == key:
                    ret = os.path.join(dirpath, filename)
                    return ret
        if ret is None:
            msg = 'a shapefile with key "{0}" was not found under the directory: {1}'.format(key, self.path)
            raise ValueError(msg)

    def iter_geoms(self, key=None, select_uid=None, path=None, load_geoms=True, uid=None, select_sql_where=None,
                   slc=None, dest_crs=None):
        """
        See documentation for :class:`~ocgis.GeomCabinetIterator`.
        """

        # ensure select ugid is in ascending order
        if select_uid is not None:
            test_select_ugid = list(deepcopy(select_uid))
            test_select_ugid.sort()
            if test_select_ugid != list(select_uid):
                raise ValueError('"select_uid" must be sorted in ascending order.')

        # get the path to the output shapefile
        shp_path = self._get_path_by_key_or_direct_path_(key=key, path=path)

        # get the source CRS
        meta = self.get_meta(path=shp_path)

        # open the target shapefile
        ds = ogr.Open(shp_path)
        try:
            # return the features iterator
            features = self._get_features_object_(ds, uid=uid, select_uid=select_uid, select_sql_where=select_sql_where)
            for ctr, feature in enumerate(features):
                # With a slice passed, ...
                if slc is not None:
                    # ... iterate until start is reached.
                    if ctr < slc[0]:
                        continue
                    # ... stop if we have reached the stop.
                    elif ctr == slc[1]:
                        raise StopIteration

                ogr_geom = feature.GetGeometryRef()
                if dest_crs is not None:
                    ogr_geom.TransformTo(dest_crs)

                if load_geoms:
                    yld = {'geom': wkb.loads(ogr_geom.ExportToWkb())}
                else:
                    yld = {}
                items = feature.items()
                properties = OrderedDict([(key, items[key]) for key in feature.keys()])
                yld.update({'properties': properties})

                if ctr == 0:
                    uid, add_uid = get_uid_from_properties(properties, uid)
                    # The properties schema needs to be updated to account for the adding of a unique identifier.
                    if add_uid:
                        meta['schema']['properties'][uid] = 'int'
                else:
                    add_uid = None

                # add the unique identifier if required
                if add_uid:
                    properties[uid] = ctr + 1
                # ensure the unique identifier is an integer
                else:
                    properties[uid] = int(properties[uid])

                yield yld
            try:
                assert ctr >= 0
            except UnboundLocalError:
                # occurs if there were not feature returned by the iterator. raise a more clear exception.
                msg = 'No features returned from target shapefile. Were features appropriately selected?'
                raise ValueError(msg)
        finally:
            # close the dataset object
            ds.Destroy()
            ds = None

    def _get_path_by_key_or_direct_path_(self, key=None, path=None):
        """
        :param str key:
        :param str path:
        """
        # path to the target shapefile
        if key is None:
            try:
                assert path != None
            except AssertionError:
                raise ValueError('If no key is passed, then a path must be provided.')
            shp_path = path
        else:
            shp_path = self.get_shp_path(key)
        # make sure requested geometry exists
        if not os.path.exists(shp_path):
            msg = 'Requested geometry with path "{0}" does not exist in the file system.'.format(shp_path)
            raise RuntimeError(msg)
        return shp_path

    @staticmethod
    def _get_features_object_(ds, uid=None, select_uid=None, select_sql_where=None):
        """
        :param ds: Path to shapefile.
        :type ds: Open OGR dataset object
        :param str uid: The unique identifier to use during SQL selection.
        :param sequence select_uid: Sequence of integers mapping to unique geometry identifiers.
        :param str select_sql_where: A string suitable for insertion into a SQL WHERE statement. See http://www.gdal.org/ogr_sql.html
         for documentation (section titled "WHERE").

        >>> select_sql_where = 'STATE_NAME = "Wisconsin"'

        :returns: A layer object with selection applied if ``select_uid`` is not ``None``.
        :rtype: :class:`osgeo.ogr.Layer`
        """

        # get the geometries
        lyr = ds.GetLayerByIndex(0)
        lyr.ResetReading()
        if select_uid is not None or select_sql_where is not None:
            lyr_name = lyr.GetName()
            if select_sql_where is not None:
                sql = 'SELECT * FROM "{0}" WHERE {1}'.format(lyr_name, select_sql_where)
            elif select_uid is not None:
                # format where statement different for singletons
                if len(select_uid) == 1:
                    sql_where = '{0} = {1}'.format(uid, select_uid[0])
                else:
                    sql_where = '{0} IN {1}'.format(uid, tuple(select_uid))
                sql = 'SELECT * FROM "{0}" WHERE {1}'.format(lyr_name, sql_where)
            features = ds.ExecuteSQL(sql)
        else:
            features = lyr
        return features


class GeomCabinetIterator(object):
    """
    Iterate over geometries from a shapefile specified by ``key`` or ``path``.

    >>> sc = GeomCabinet()
    >>> geoms = sc.iter_geoms('state_boundaries', select_uid=[1, 48])
    >>> len(list(geoms))
    2

    :param key: Unique key identifier for a shapefile contained in the :class:`~ocgis.GeomCabinet` directory.
    :type key: str

    >>> key = 'state_boundaries'

    :param select_uid: Sequence of unique identifiers to select from the target shapefile.
    :type select_uid: sequence

    >>> select_uid = [23, 24]

    :param path: Path to the target shapefile to iterate over. If ``key`` is provided it will override ``path``.
    :type path: str

    >>> path = '/path/to/shapefile.shp'

    :param bool load_geoms: If ``False``, do not load geometries, excluding the ``'geom'`` key from the output
     dictionary.
    :param bool as_spatial_dimension: If ``True``, yield spatial dimension (:class:`~ocgis.SpatialDimension`)
     objects.
    :param str uid: The name of the attribute containing the unique identifier. If ``None``,
     :attr:`ocgis.env.DEFAULT_GEOM_UID` will be used if present. If no unique identifier is found, add one with name
     :attr:`ocgis.env.DEFAULT_GEOM_UID`.
    :param str select_sql_where: A string suitable for insertion into a SQL WHERE statement. See http://www.gdal.org/ogr_sql.html
     for documentation (section titled "WHERE").

    >>> select_sql_where = 'STATE_NAME = "Wisconsin"'

    :param slice: A two-element integer sequence: [start, stop].

    >>> slc = [0, 5]

    :type slice: sequence
    :raises: ValueError, RuntimeError
    :rtype: dict
    """

    def __init__(self, key=None, select_uid=None, path=None, load_geoms=True, uid=None, select_sql_where=None,
                 slc=None, dest_crs=None):
        self.key = key
        self.path = path
        self.select_uid = select_uid
        self.load_geoms = load_geoms
        self.uid = uid
        self.select_sql_where = select_sql_where
        self.slc = slc
        self.dest_crs = dest_crs
        self.sc = GeomCabinet()

    def __iter__(self):
        """
        Return an iterator as from :meth:`ocgis.GeomCabinet.iter_geoms`.
        """

        for row in self.sc.iter_geoms(key=self.key, select_uid=self.select_uid, path=self.path,
                                      load_geoms=self.load_geoms, uid=self.uid, select_sql_where=self.select_sql_where,
                                      slc=self.slc, dest_crs=self.dest_crs):
            yield row

    def __len__(self):
        # get the path to the output shapefile
        shp_path = self.sc._get_path_by_key_or_direct_path_(key=self.key, path=self.path)

        if self.slc is not None:
            ret = self.slc[1] - self.slc[0]
        elif self.select_uid is not None:
            ret = len(self.select_uid)
        else:
            # get the geometries
            ds = ogr.Open(shp_path)
            try:
                features = self.sc._get_features_object_(ds, uid=self.uid, select_uid=self.select_uid,
                                                         select_sql_where=self.select_sql_where)
                ret = len(features)
            finally:
                ds.Destroy()
                ds = None
        return ret


def get_uid_from_properties(properties, uid):
    """
    :param dict properties: A dictionary of properties with key corresponding to property names.
    :param str uid: The unique identifier to search for. If ``None``, default to :attr:`~ocgis.env.DEFAULT_GEOM_UID`.
    :returns: A tuple containing the name of the unique identifier and a boolean indicating if a unique identifier needs
     to be generated.
    :rtype: (str, bool)
    :raises: ValueError
    """

    if uid not in properties:
        msg = 'The unique identifier "{0}" was not found in the properties dictionary: {1}'.format(uid, properties)
        raise ValueError(msg)

    # if there is a unique identifier in the properties dictionary, ensure it may be converted to an integer data type.
    if uid is not None:
        try:
            int(properties[uid])
        except ValueError:
            msg = 'The unique identifier "{0}" may not be converted to an integer data type.'.format(uid)
            raise ValueError(msg)

    # if there is no unique identifier, the default identifier name will be assigned.
    add_uid = False

    return uid, add_uid
