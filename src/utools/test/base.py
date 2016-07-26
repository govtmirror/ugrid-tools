import os
import shutil
import subprocess
import tempfile
from unittest import TestCase

from logbook import DEBUG

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

    def get_temporary_file_path(self, fn):
        return os.path.join(self.path_current_tmp, fn)

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
