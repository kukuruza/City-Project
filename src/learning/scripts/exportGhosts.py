import logging
import os, sys
sys.path.insert(0, os.path.abspath('..'))
from setupHelper import setupLogging
import exporting


setupLogging ('log/learning/clusterGhosts.log', logging.INFO, 'a')

in_db_path   = 'databases/wr-e0.3.db'
filters_path = 'clustering/filters/angles.json'
out_dir      = 'clustering/test'

# original way: directories with image patches
#exporting.collectGhostsTask (in_db_path, filters_path, out_dir)

# new way -- hdf5 files:
params={'constraint': 'name == "truck"', 'write_samples': 1}
exporting.collectGhostsTaskHDF5 (in_db_path, filters_path, out_dir, params)
