import logging
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
from helperSetup import setupLogging, dbInit
import helperH5
import h5py


setupLogging ('log/learning/exportGhosts.log', logging.DEBUG, 'a')

in_dataset = 'clustering/try-hdf5/testing-40x30'

with h5py.File (os.path.join(os.getenv('CITY_DATA_PATH'), in_dataset + '.h5')) as f:
    helperH5.viewPatches (f, {'random': True, 'scale': 4})
