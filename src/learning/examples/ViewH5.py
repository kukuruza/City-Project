import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import h5py
from learning.helperSetup import setupLogging, atcity
from learning.helperH5    import viewPatches, crop, exportLabels


setupLogging ('log/learning/exportGhosts.log', logging.DEBUG, 'a')

in_dataset = 'data/patches/try-hdf5/testing-40x30'

# with h5py.File (atcity(in_dataset + '.h5')) as f:
#     with open (atcity('truth.txt'), 'w') as f_out:
#         exportLabels (f, f_out)
# sys.exit()

# with h5py.File (atcity(out_dataset + '.h5')) as f_out:
#     with h5py.File (atcity(in_dataset + '.h5')) as f_in:
#         crop (f_in, f_out, 20, {'chunk': 20})

with h5py.File (atcity(in_dataset + '.h5')) as f:
    viewPatches (f, {'random': True, 'scale': 4})
