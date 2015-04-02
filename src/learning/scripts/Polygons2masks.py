import logging
import os, sys
sys.path.insert(0, os.path.abspath('..'))
from setupHelper import setupLogging
import processing


setupLogging ('log/learning/clusterGhosts.log', logging.INFO, 'a')

db_in_path   = 'datasets/labelme/Databases/src-pairs.db'
db_out_path   = 'datasets/labelme/Databases/src-pairs-2.db'

processing.dbPolygonsToMasks (db_in_path, db_out_path)
