import logging
import os, sys
sys.path.insert(0, os.path.abspath('..'))
from utilities import setupLogging
import processing


setupLogging ('log/learning/clusterGhosts.log', logging.INFO, 'a')

db_in_path   = 'datasets/labelme/Databases/src-frames-2.db'
filters_path = 'clustering/filters/byname_24x18.json'
out_dir      = 'clustering/sparse-byname_24x18-2'

processing.dbPolygonsToMasks (db_in_path, filters_path)
