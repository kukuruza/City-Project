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
from processing import Processor
from utilities import setupLogging


if __name__ == '__main__':

    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        raise Exception ('Set environmental variables CITY_PATH, CITY_DATA_PATH')

    setupLogging ('log/learning/processDb.log', logging.INFO, 'a')

    CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')
#    db_in_path  = op.join (CITY_DATA_PATH, 'labelme/Databases/src-frames.db')
#    db_out_path = op.join (CITY_DATA_PATH, 'databases/wratio-p0.2.db')
    db_in_path  = op.join (CITY_DATA_PATH, 'datasets/sparse/578-Mar15-10h/Databases/src-ds2.5-dp12.0.db')
    db_out_path = op.join (CITY_DATA_PATH, 'datasets/sparse/578-Mar15-10h/Databases/filt-ds2.5-dp12.0.db')

    params = {'geom_maps_dir': op.join (CITY_DATA_PATH, 'models/cam578/'),
              'debug_show': False,
              'expand_perc': 0,
              'keep_ratio': False,
              'border_thresh_perc': 0.005,
              'min_width_thresh': 10 }

    processor = Processor (params)
    processor.processDb (db_in_path, db_out_path)

    dbAssignOrientations (db_out_path, db_out_path, params)

    