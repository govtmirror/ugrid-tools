"""Generate arrays for file paths."""
from os import listdir
from os.path import join

DIR = "/media/benkoziol/Extra Drive 1/data/nfie/storage/catchment_esmf_format"
# DIR = "/media/benkoziol/Extra Drive 1/data/nfie/example-weights-files"
ARR = "dstFilenames"
# ARR = "weightFilenames"

template = "{}({}) = '{}'"

fns = listdir(DIR)
fns.sort()

for ii, fn in enumerate(fns, start=1):
    print template.format(ARR, ii, join(DIR, fn))

print max([len(f) for f in fns]) + len(DIR) + 1
