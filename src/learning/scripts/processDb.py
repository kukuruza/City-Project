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
from processing import dbFilter, dbExpandBboxes
from utilities import setupLogging


if __name__ == '__main__':

    setupLogging ('log/learning/processDb.log', logging.INFO, 'a')

    CITY_DATA_PATH = get_CITY_DATA_PATH()
    db_in_path  = op.join (CITY_DATA_PATH, 'databases/sparse-Mar18-wb-wr.db')
    db_out_path = op.join (CITY_DATA_PATH, 'databases/sparse-Mar18-wb-wr-ex0.3.db')
    #db_in_path  = op.join (CITY_DATA_PATH, 'datasets/sparse/Databases/578-Jan22-14h/src-ds2.5-dp12.0.db')
    #db_out_path = op.join (CITY_DATA_PATH, 'datasets/sparse/Databases/578-Jan22-14h/filt-ds2.5-dp12.0.db')

    #params = {'geom_maps_template': op.join (CITY_DATA_PATH, 'models/cam578/Jan22-14h-'),
    #          'debug_show': False,
    #          'expand_perc': 0.1,
    #          'keep_ratio': True,
    #          'border_thresh_perc': 0.005,
    #          'min_width_thresh': 10 }

    params = {'debug_show': True,
              'keep_ratio': True,
              'expand_perc': 0.3 }

    #dbFilter (db_in_path, db_out_path, params)
    dbExpandBboxes (db_in_path, db_out_path, params)
    #dbAssignOrientations (db_out_path, db_out_path, params)

    