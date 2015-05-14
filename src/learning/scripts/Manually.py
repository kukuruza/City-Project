import logging
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
from setupHelper import setupLogging
from dbBase import Processor


setupLogging ('log/learning/Manually.log', logging.INFO, 'a')

db_in_path =  'datasets/sparse/Databases/119-Apr09-13h/clas.db'
db_out_path = 'datasets/sparse/Databases/119-Apr09-13h/test.db'

Processor()\
    .open (db_in_path, db_out_path)\
    .show ()\
    .examine ()\
    .classifyName ({ 'car_constraint': 'name = "sedan"',
                      'disp_scale': 2
                    })\
    .classifyColor ({ 'car_constraint': 'name = "sedan"',
                      'disp_scale': 2
                    })\
    .close ()


