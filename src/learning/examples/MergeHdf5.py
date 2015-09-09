import logging
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
from helperSetup import setupLogging
import helperH5
import h5py


setupLogging ('log/learning/mergeHdf5.log', logging.INFO, 'a')

# combine positive and negative into one hdf5 file
h5_in_path1 = 'clustering/try-hdf5/training-negatives.h5'
h5_in_path2 = 'clustering/try-hdf5/572-578-e0.1.h5'
h5_out_path = 'clustering/try-hdf5/training-40x30.h5'
with h5py.File (os.path.join(os.getenv('CITY_DATA_PATH'), h5_in_path1)) as in_f1:
    with h5py.File (os.path.join(os.getenv('CITY_DATA_PATH'), h5_in_path2)) as in_f2:
        with h5py.File (os.path.join(os.getenv('CITY_DATA_PATH'), h5_out_path)) as out_f:
            helperH5.mergeH5 (in_f1, in_f2, out_f, {'shuffle': True, 'multiple': 100})
