import itertools
import os
import shutil
import subprocess
import tempfile
from unittest import SkipTest
from unittest import TestCase

import netCDF4 as nc
import numpy as np
from logbook import DEBUG

from utools import env
from utools.constants import UgridToolsConstants
from utools.helpers import nc_scope
from utools.logging import log


class AbstractUToolsTest(TestCase):
    key = UgridToolsConstants.PROJECT_PREFIX

    @property
    def log(self):
        return log

    @property
    def path_bin(self):
        path = os.path.split(__file__)[0]
        path = os.path.join(path, 'bin')
        return path

    @property
    def path_nhd_seamless_file_geodatabase(self):
        return env.TEST_NHD_SEAMLESS_FILE_GDB

    def assertNcEqual(self, uri_src, uri_dest, check_types=True, close=False, metadata_only=False,
                      ignore_attributes=None, ignore_variables=None):
        """
        Assert two netCDF files are equal according to the test criteria.

        :param str uri_src: A URI to a source file.
        :param str uri_dest: A URI to a destination file.
        :param bool check_types: If ``True``, check data types of variable arrays.
        :param bool close: If ``False``, use exact value comparisons without a tolerance.
        :param bool metadata_only: If ``False``, check array values associated with variables. If ``True``, only check
         metadata values and not value arrays.
        :param dict ignore_attributes: Select which attributes to ignore when testing. Keys are associated with variable
         names. The exception is for dataset-level attributes which are selected with the key `'global'`.

        >>> ignore_attributes = {'global': ['history']}

        :param list ignore_variables: A list of variable names to ignore.
        """

        ignore_variables = ignore_variables or []

        src = nc.Dataset(uri_src)
        dest = nc.Dataset(uri_dest)

        ignore_attributes = ignore_attributes or {}

        try:
            self.assertEqual(src.data_model, dest.data_model)

            for dimname, dim in src.dimensions.iteritems():
                self.assertEqual(len(dim), len(dest.dimensions[dimname]))
            self.assertEqual(set(src.dimensions.keys()), set(dest.dimensions.keys()))

            for varname, var in src.variables.iteritems():

                if varname in ignore_variables:
                    continue

                dvar = dest.variables[varname]

                var_value = var[:]
                dvar_value = dvar[:]

                try:
                    if not metadata_only:
                        if var_value.dtype == object:
                            for idx in range(var_value.shape[0]):
                                if close:
                                    self.assertNumpyAllClose(var_value[idx], dvar_value[idx])
                                else:
                                    self.assertNumpyAll(var_value[idx], dvar_value[idx], check_arr_dtype=check_types)
                        else:
                            try:
                                if close:
                                    self.assertNumpyAllClose(var_value, dvar_value)
                                else:
                                    self.assertNumpyAll(var_value, dvar_value, check_arr_dtype=check_types)
                            except AssertionError as e:
                                msg = e.message + '; variable name is "{}"'.format(varname)
                                raise AssertionError(msg)
                except (AssertionError, AttributeError):
                    # Zero-length netCDF variables should not be tested for value equality. Values are meaningless and
                    # only the attributes should be tested for equality.
                    if len(dvar.dimensions) == 0:
                        self.assertEqual(len(var.dimensions), 0)
                    else:
                        raise

                if check_types:
                    self.assertEqual(var_value.dtype, dvar_value.dtype)

                # check values of attributes on all variables
                for k, v in var.__dict__.iteritems():
                    try:
                        to_test_attr = getattr(dvar, k)
                    except AttributeError:
                        # if the variable and attribute are flagged to ignore, continue to the next attribute
                        if dvar._name in ignore_attributes:
                            if k in ignore_attributes[dvar._name]:
                                continue

                        # notify if an attribute is missing
                        msg = 'The attribute "{0}" is not found on the variable "{1}" for URI "{2}".' \
                            .format(k, dvar._name, uri_dest)
                        raise AttributeError(msg)
                    try:
                        self.assertNumpyAll(v, to_test_attr)
                    except AttributeError:
                        self.assertEqual(v, to_test_attr)

                # check values of attributes on all variables
                for k, v in dvar.__dict__.iteritems():
                    try:
                        to_test_attr = getattr(var, k)
                    except AttributeError:
                        # if the variable and attribute are flagged to ignore, continue to the next attribute
                        if var._name in ignore_attributes:
                            if k in ignore_attributes[var._name]:
                                continue

                        # notify if an attribute is missing
                        msg = 'The attribute "{0}" is not found on the variable "{1}" for URI "{2}".' \
                            .format(k, var._name, uri_src)
                        raise AttributeError(msg)
                    try:
                        self.assertNumpyAll(v, to_test_attr)
                    except AttributeError:
                        self.assertEqual(v, to_test_attr)

                self.assertEqual(var.dimensions, dvar.dimensions)

            sets = [set(xx.variables.keys()) for xx in [src, dest]]
            for ignore_variable, s in itertools.product(ignore_variables, sets):
                try:
                    s.remove(ignore_variable)
                except KeyError:
                    # likely missing in one or the other
                    continue
            self.assertEqual(*sets)

            if 'global' not in ignore_attributes:
                self.assertDictEqual(src.__dict__, dest.__dict__)
            else:
                for k, v in src.__dict__.iteritems():
                    if k not in ignore_attributes['global']:
                        to_test = dest.__dict__[k]
                        try:
                            self.assertNumpyAll(v, to_test)
                        except AttributeError:
                            self.assertEqual(v, to_test)
        finally:
            src.close()
            dest.close()

    def assertNumpyAll(self, arr1, arr2, check_fill_value_dtype=True, check_arr_dtype=True, check_arr_type=True,
                       rtol=None):
        """
        Asserts arrays are equal according to the test criteria.

        :param arr1: An array to compare.
        :type arr1: :class:`numpy.ndarray`
        :param arr2: An array to compare.
        :type arr2: :class:`numpy.ndarray`
        :param bool check_fill_value_dtype: If ``True``, check that the data type for masked array fill values are equal.
        :param bool check_arr_dtype: If ``True``, check the data types of the arrays are equal.
        :param bool check_arr_type: If ``True``, check the types of the incoming arrays.

        >>> type(arr1) == type(arr2)

        :param places: If this is a float value, use a "close" data comparison as opposed to exact comparison. The
         value is the test tolerance. See http://docs.scipy.org/doc/numpy/reference/generated/numpy.allclose.html.
        :type places: float

        >>> places = 1e-4

        :raises: AssertionError
        """

        if check_arr_type:
            self.assertEqual(type(arr1), type(arr2))
        self.assertEqual(arr1.shape, arr2.shape)
        if check_arr_dtype:
            self.assertEqual(arr1.dtype, arr2.dtype)
        if isinstance(arr1, np.ma.MaskedArray) or isinstance(arr2, np.ma.MaskedArray):
            data_to_check = (arr1.data, arr2.data)
            self.assertTrue(np.all(arr1.mask == arr2.mask))
            if check_fill_value_dtype:
                self.assertEqual(arr1.fill_value, arr2.fill_value)
            else:
                self.assertTrue(np.equal(arr1.fill_value, arr2.fill_value.astype(arr1.fill_value.dtype)))
        else:
            data_to_check = (arr1, arr2)

        # Check the data values.
        if rtol is None:
            to_assert = np.all(data_to_check[0] == data_to_check[1])
        else:
            to_assert = np.allclose(data_to_check[0], data_to_check[1], rtol=rtol)
        self.assertTrue(to_assert)

    def assertNumpyAllClose(self, arr1, arr2):
        """
        Asserts arrays are close according to the test criteria.

        :param arr1: An array to compare.
        :type arr1: :class:`numpy.ndarray`
        :param arr2: An array to compare.
        :type arr2: :class:`numpy.ndarray`
        :raises: AssertionError
        """

        self.assertEqual(type(arr1), type(arr2))
        self.assertEqual(arr1.shape, arr2.shape)
        if isinstance(arr1, np.ma.MaskedArray) or isinstance(arr2, np.ma.MaskedArray):
            self.assertTrue(np.allclose(arr1.data, arr2.data))
            self.assertTrue(np.all(arr1.mask == arr2.mask))
            self.assertEqual(arr1.fill_value, arr2.fill_value)
        else:
            self.assertTrue(np.allclose(arr1, arr2))

    def get_temporary_file_path(self, fn):
        return os.path.join(self.path_current_tmp, fn)

    def handle_no_geodatabase(self):
        if self.path_nhd_seamless_file_geodatabase is None \
                or not os.path.exists(self.path_nhd_seamless_file_geodatabase):
            raise SkipTest('Path to NHD seamless file geodatabase does not exist.')

    def ncdump(self, path, header=True):
        cmd = ['ncdump']
        if header:
            cmd.append('-h')
        cmd.append(path)
        subprocess.check_call(cmd)

    def nc_scope(self, *args, **kwargs):
        return nc_scope(*args, **kwargs)

    def set_debug(self):
        self.log.level = DEBUG

    def setUp(self):
        self.path_current_tmp = tempfile.mkdtemp(prefix='{0}_test_'.format(self.key))

    def shortDescription(self):
        return None

    def tearDown(self):
        shutil.rmtree(self.path_current_tmp)


def attr(*args, **kwargs):
    """
    Decorator that adds attributes to classes or functions for use with the Attribute (-a) plugin.

    http://nose.readthedocs.org/en/latest/plugins/attrib.html
    """

    def wrap_ob(ob):
        for name in args:
            setattr(ob, name, True)
        for name, value in kwargs.iteritems():
            setattr(ob, name, value)
        return ob

    return wrap_ob
