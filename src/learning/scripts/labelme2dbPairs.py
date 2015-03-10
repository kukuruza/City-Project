#
# wrapper around folder2pairs
# set up logging, paths, and call the function
#

import logging
import sys
import os, os.path as op
sys.path.insert(0, os.path.abspath('../labelme'))
from labelme2db import folder2pairs
from utilities import setupLogging


if __name__ == '__main__':

    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        raise Exception ('Set environmental variables CITY_PATH, CITY_DATA_PATH')

    setupLogging ('log/learning/analyzePairs.log', logging.INFO)

    folder = 'cam572-5pm-pairs'
    db_path = op.join(os.getenv('CITY_DATA_PATH'), 'labelme/Databases/src-pairs.db')

    params = { 'backimage_file': 'camdata/cam572/5pm/models/backimageTwice.png' }

    folder2pairs (folder, db_path, params)
