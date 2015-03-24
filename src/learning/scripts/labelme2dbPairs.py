import logging
import sys
import os, os.path as op
sys.path.insert(0, os.path.abspath('../labelme'))
from labelme2db import folder2pairs
from utilities import setupLogging, get_CITY_DATA_PATH


if __name__ == '__main__':

    CITY_DATA_PATH = get_CITY_DATA_PATH()
    setupLogging ('log/learning/analyzePairs.log', logging.INFO)

    folder = 'cam572-5pm-pairs'
    db_path = op.join(os.getenv('CITY_DATA_PATH'), 'datasets/labelme/Databases/src-pairs-2.db')

    params = { 'backimage_file': 'camdata/cam572/5pm/models/backimageTwice.png',
               'labelme_dir': 'datasets'
             }

    folder2pairs (folder, db_path, params)
