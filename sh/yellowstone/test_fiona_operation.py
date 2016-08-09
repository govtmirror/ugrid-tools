import os

import fiona

SOURCE_SHP = os.environ['SOURCE_SHP']

with fiona.open(SOURCE_SHP) as source:
    assert len(list(source)) > 0
