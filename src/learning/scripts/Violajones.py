import logging
import sys, os
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
import processing
from setupHelper import setupLogging
from dbBase import Processor


setupLogging ('log/learning/Violajones.log', logging.WARNING, 'a')

db_in_path  = 'datasets/labelme/Databases/572-Oct30-17h-pair/vj1.db'
fromback_path = 'datasets/labelme/Databases/572-Oct30-17h-pair/fromback.db'

db_out_path = 'datasets/labelme/Databases/572-Oct30-17h-pair/vj1-and-fromback-thres-test.db'


Processor()\
    .open (db_in_path, db_out_path)\
    .merge (fromback_path, {'debug_show': True})\
    .filterSize ({'size_map_path': 'models/cam572/mapSize.tiff',
                  'size_acceptance': 2, 
                  'debug_show': True})\
    .cluster    ({'threshold': 0.7, 
                  'debug_show': True})\
    .close()

#params = {'score_map_path': 'models/cam572/mapFromback.tiff',
#          'debug_show': True,
#          }
#processing.dbMaskScores (db_in_path, db_out_path, params)

#processing.dbThresholdScore (db_in_path, db_out_path, params)
