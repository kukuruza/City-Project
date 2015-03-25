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
import sys
import os, os.path as op
sys.path.insert(0, os.path.abspath('..'))
import processing
from utilities import setupLogging, get_CITY_DATA_PATH


if __name__ == '__main__':

    setupLogging ('log/learning/processDb.log', logging.INFO, 'a')

    CITY_DATA_PATH = get_CITY_DATA_PATH()
    db_in_path  = op.join (CITY_DATA_PATH, 'databases/color-wr-p0.3.db')
    db_out_path = op.join (CITY_DATA_PATH, 'databases/color-wr-p0.3.db')


    #params = {'geom_maps_template': op.join (CITY_DATA_PATH, 'models/cam671/'),
    #          'debug_show': False,
    #          'border_thresh_perc': -0.1,
    #          'min_width_thresh': 10 }
    #processing.dbFilter (db_in_path, db_out_path, params)
    #processing.dbAssignOrientations (db_out_path, db_out_path, params)


    params = {'debug_show': True,
              'keep_ratio': True,
              'expand_perc': 0.3 }
    processing.dbExpandBboxes (db_in_path, db_out_path, params)


    #processing.dbCustomScript (db_in_path, db_out_path)


    #params = { 'masks_dir': 'datasets/sparse/Masks/572-Oct28-10h/' }
    #processing.dbMove (db_in_path, db_out_path, params)


    