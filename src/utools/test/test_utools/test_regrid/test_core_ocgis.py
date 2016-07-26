import os

import numpy as np

from utools.regrid.core_ocgis import create_merged_weights
from utools.test.base import AbstractUToolsTest


class Test(AbstractUToolsTest):
    def test_create_merged_weights(self):
        path_esmf_format = os.path.join(self.path_bin, 'test_esmf_format.nc')
        path_weights_nc = os.path.join(self.path_bin, 'test_weights.nc')
        master_weights = self.get_temporary_file_path('master_weights.nc')

        weight_files = [path_weights_nc, path_weights_nc]
        esmf_unstructured = [path_esmf_format, path_esmf_format]

        create_merged_weights(weight_files, esmf_unstructured, master_weights)

        with self.nc_scope(master_weights) as ds:
            # The combined file has 86 elements. Each individual file had 43.
            self.assertEqual(len(ds.dimensions['elementCount']), 86)
            # The maximum index should not exceed 87.
            self.assertTrue(np.all(ds.variables['row'][:] < 87))
            # The maximum index should be greater than the element count in the original file.
            self.assertTrue(np.any(ds.variables['row'][:] > 43))

