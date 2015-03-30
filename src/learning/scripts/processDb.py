import logging
import sys, os
sys.path.insert(0, os.path.abspath('..'))
import processing
from setup_helper import setupLogging


setupLogging ('log/learning/processDb.log', logging.INFO, 'a')

db_in_path  = 'datasets/labelme/Databases/src-frames.db'
db_out_path = 'datasets/labelme/Databases/filt-frames.db'


# needs params
#processing.dbAssignOrientations (db_out_path, db_out_path, params)


params = {'geom_maps_template': 'models/cam572/',
          'debug_show': True,
          'border_thresh_perc': -0.01,
          'min_width_thresh': 10 }
processing.dbFilter (db_in_path, db_out_path, params)


#params = {'debug_show': False,
#          'keep_ratio': True,
#          'expand_perc': 0.1 }
#processing.dbExpandBboxes (db_in_path, db_out_path, params)


#processing.dbCustomScript (db_in_path, db_out_path)


#params = { 'masks_dir': 'datasets/sparse/Masks/572-Oct28-10h/' }
#processing.dbMove (db_in_path, db_out_path, params)
