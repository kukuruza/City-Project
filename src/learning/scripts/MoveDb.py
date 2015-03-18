import logging
import sys
import os, os.path as op
sys.path.insert(0, os.path.abspath('..'))
from processing import dbMove
from utilities import setupLogging, getCalibration


if __name__ == '__main__':

    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        raise Exception ('Set environmental variables CITY_PATH, CITY_DATA_PATH')

    setupLogging ('log/learning/MoveDb.log', logging.INFO, 'a')

    CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')
    db_in_path  = op.join (CITY_DATA_PATH, 'datasets/labelme/Databases/src-pairs.db')
    db_out_path = op.join (CITY_DATA_PATH, 'datasets/labelme/Databases/src-pairs-mv.db')

    params = { 'images_dir': 'datasets/labelme/Images/cam572-5pm-pairs' }

    dbMove (db_in_path, db_out_path, params)
    