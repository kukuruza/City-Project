#
# wrapper around Processor.processDb()
# set up logging, paths, and call the function
#
# params:
#   border_thresh_perc  0.03
#   expand_perc         0.1
#   target_ratio        0.75
#   keep_ratio          False
#   size_acceptance     (0.4, 2)
#   ratio_acceptance    (0.4, 1.5)
#   sizemap_dilate      21
#   debug_show          False
#   debug_sizemap       False
#   geom_maps_dir       
#

import logging
import sys, os
sys.path.insert(0, os.path.abspath('..'))
import processing
from setup_helper import setupLogging


setupLogging ('log/learning/processDb.log', logging.INFO, 'a')

db_in_path  = 'datasets/sparse/Databases/578-Jan22-14h/filt-ds2.5-dp12.0.db'
db_out_path = 'datasets/sparse/Databases/578-Jan22-14h/filt-ds2.5-dp12.0-15.db'


# needs params
#processing.dbAssignOrientations (db_out_path, db_out_path, params)


params = {'geom_maps_template': 'models/cam671/',
          'debug_show': False,
          'border_thresh_perc': -0.01,
          'min_width_thresh': 15 }
processing.dbFilter (db_in_path, db_out_path, params)


#params = {'debug_show': False,
#          'keep_ratio': True,
#          'expand_perc': 0.1 }
#processing.dbExpandBboxes (db_in_path, db_out_path, params)


#processing.dbCustomScript (db_in_path, db_out_path)


#params = { 'masks_dir': 'datasets/sparse/Masks/572-Oct28-10h/' }
#processing.dbMove (db_in_path, db_out_path, params)
