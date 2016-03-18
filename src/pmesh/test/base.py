import os
import shutil
import subprocess
import tempfile
from unittest import TestCase

import logbook

from pmesh.helpers import nc_scope


class AbstractNFIETest(TestCase):
    key = 'pmesh'
    logging_level = logbook.INFO
    log = logbook.Logger(key, level=logging_level)

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

    def set_debug(self, value):
        if value:
            self.log.level = logbook.DEBUG
        else:
            self.log.level = logbook.INFO

    def setUp(self):
        self.set_debug(False)
        self.path_current_tmp = tempfile.mkdtemp(prefix='{0}_test_'.format(self.key))

    def shortDescription(self):
        return None

    def tearDown(self):
        shutil.rmtree(self.path_current_tmp)
