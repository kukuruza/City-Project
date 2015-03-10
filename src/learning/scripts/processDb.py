#
# wrapper around Processor.processDb()
# set up logging, paths, and call the function
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

    setupLogging ('log/learning/processDb.log', logging.INFO)

    CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')
    db_in_path  = op.join (CITY_DATA_PATH, 'labelme/Databases/src-all.db')
    db_out_path = op.join (CITY_DATA_PATH, 'databases/w-ratio.db')

    params = {'geom_maps_dir': op.join (CITY_DATA_PATH, 'models/cam572/'),
              'debug_show': False,
              'keep_ratio': True,
              'border_thresh_perc': -0.01 }

    processor = Processor (params)
    processor.processDb (db_in_path, db_out_path)
    