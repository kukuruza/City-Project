import logging
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
from setupHelper import setupLogging
from dbAll import Processor

setupLogging ('log/learning/Manually.log', logging.INFO, 'a')

db_in_path =  'datasets/labelme/Databases/572-Nov28-10h-pair/detected/fromback-dr8.db'
db_true_path =  'datasets/labelme/Databases/572-Nov28-10h-pair/parsed.db'

print (Processor(db_in_path).evaluateDetector(db_true_path, {'debug_show': False}))
