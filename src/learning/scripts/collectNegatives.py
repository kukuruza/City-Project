#
# wrapper around NegativesGrayspots.processDb()
# set up logging, paths, and call the function
#

import logging
import sys
import os, os.path as op
sys.path.insert(0, os.path.abspath('..'))
from negatives import NegativesGrayspots
from utilities import setupLogging


if __name__ == '__main__':

    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        raise Exception ('Set environmental variables CITY_PATH, CITY_DATA_PATH')
    CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')

    setupLogging ('log/learning/collectNegatives.log', logging.INFO)

    db_path      = op.join (CITY_DATA_PATH, 'labelme/Databases/src-all.db')
    filters_path = op.join (CITY_DATA_PATH, 'clustering/filters/neg_by_type.json')
    out_dir      = op.join (CITY_DATA_PATH, 'clustering/neg_by_type')

    processor = NegativesGrayspots ()
    processor.processDb (db_path, filters_path, out_dir)
