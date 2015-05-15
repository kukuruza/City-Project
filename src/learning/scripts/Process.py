import logging
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
from setupHelper import setupLogging
from dbAll import Processor


setupLogging ('log/learning/Manually.log', logging.INFO, 'a')

db_in_path =  'datasets/labelme/Databases/572-Nov28-10h-pair/detected/mhr0.995-mfar0.7-wtr0.95.db'
db_out_path = 'datasets/labelme/Databases/572-Nov28-10h-pair/detected/mhr0.995-mfar0.7-wtr0.95-filt.db'

Processor(db_in_path, db_out_path)\
    .merge ('datasets/labelme/Databases/572-Nov28-10h-pair/detected/fromback-dr8.db')\
    .filterSize ( {'size_map_path': 'models/cam572/mapSize.tiff', 'debug_show': False } )\
    .thresholdScore ({'threshold': 0.7, 'debug_show': True } )\
    .show()\
    .commit()

#    .clusterBboxes ({'threshold': 0.7, 'debug_show': True})\

