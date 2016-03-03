import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import h5py
from learning.helperSetup import setupLogging, atcity
from learning.helperH5    import mergeH5


setupLogging ('log/learning/mergeHdf5.log', logging.INFO, 'a')

# combine positive and negative into one hdf5 file
h5_in_file1 = 'patches/try-hdf5/training-negatives.h5'
h5_in_file2 = 'patches/try-hdf5/572-578-e0.1.h5'
h5_out_file = 'patches/try-hdf5/training-40x30.h5'
with h5py.File (atcity(h5_in_file1)) as in_f1:
    with h5py.File (atcity(h5_in_file2)) as in_f2:
        with h5py.File (atcity(h5_out_file)) as out_f:
            mergeH5 (in_f1, in_f2, out_f, {'shuffle': True, 'multiple': 100})
