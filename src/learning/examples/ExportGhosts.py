import logging
import os, sys
sys.path.insert(0, os.path.abspath('..'))
from helperSetup import setupLogging, dbInit
import dbExport
import helperH5
import h5py


setupLogging ('log/learning/exportGhosts.log', logging.INFO, 'a')

in_db_path  = 'databases/671-e0.1.db'
out_dataset = 'clustering/try-hdf5/671-e0.1'
params = {'label': 1, 'resize': (40, 30), 'constraint': "name = 'sedan' AND width >= 30 AND width < 80"}

(conn, cursor) = dbInit(os.path.join(os.getenv('CITY_DATA_PATH'), in_db_path))
dbExport.collectPatches (cursor, out_dataset, params)
conn.close()

with h5py.File (os.path.join(os.getenv('CITY_DATA_PATH'), out_dataset + '.h5')) as f:
    helperH5.viewPatches (f, {'random': True, 'scale': 4})
