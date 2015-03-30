import logging
import os, sys
sys.path.insert(0, os.path.abspath('..'))
from setup_helper import setupLogging
import processing


setupLogging ('log/learning/ClusterBboxes.log', logging.INFO, 'a')

db_in_path  = 'datasets/labelme/Databases/filt-frames.db'
db_out_path = 'datasets/labelme/Databases/distinct-frames.db'

params = { 'debug_clustering': False,
           'debug_show': False,
           'threshold': 0.5 }

processing.dbClusterBboxes (db_in_path, db_out_path, params)

