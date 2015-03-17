import logging
import sys
import os, os.path as op
sys.path.insert(0, os.path.abspath('..'))
from processing import dbClassifyManually
from utilities import setupLogging, getCalibration


if __name__ == '__main__':

    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        raise Exception ('Set environmental variables CITY_PATH, CITY_DATA_PATH')

    setupLogging ('log/learning/manuallyFilterDb.log', logging.INFO, 'a')

    CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')
    db_in_path  = op.join (CITY_DATA_PATH, 'datasets/sparse/Databases/572-Oct28-10h/filt-ds2.5-dp12.0.db')
    db_out_path = op.join (CITY_DATA_PATH, 'datasets/sparse/Databases/572-Oct28-10h/clas-ds2.5-dp12.0-test.db')

    #params = { 'imagefile_start': 'datasets/sparse/572-10h/Ghosts/000521.jpg' }
    #params = { 'car_condition': 'AND name = "vehicle"' }
    params = {}

    dbClassifyManually (db_in_path, db_out_path, params)
    