import logging
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
from setupHelper import setupLogging
from dbBase import Processor


setupLogging ('log/learning/Manually.log', logging.INFO, 'a')

db_in_path =  'datasets/labelme/Databases/572-Oct30-17h-pair/vj1-and-fromback-thres.db'
db_out_path = 'datasets/sparse/Databases/119-Apr09-13h/test.db'

Processor()\
    .open (db_in_path, db_out_path)\
    .clusterBboxes ({'threshold': 0.7, 'debug_show': True})\
    .show ()\
    .close ()
