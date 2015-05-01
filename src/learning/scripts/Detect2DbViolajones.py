import logging
import os, sys
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../violajones'))
from setupHelper import setupLogging
import evaluateTask


setupLogging ('log/detector/Detect2DbViolajones.log', logging.INFO, 'a')

db_in_path = 'datasets/labelme/Databases/572/distinct-frames.db'
db_out_path = 'datasets/labelme/Databases/572/Apr01-masks-ex0.1-di0.3-er0.3.db'
model_path = 'learning/violajones/models/Apr01-masks/ex0.1-di0.3-er0.3/cascade.xml'

params = { 'debug_show': True,
           'expanded': 0.1
         }

evaluateTask.dbDetectCascade (db_in_path, db_out_path, model_path, params)
