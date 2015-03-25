import logging
import sys
import os, os.path as op
sys.path.insert(0, os.path.abspath('..'))
import processing
from utilities import setupLogging, getCalibration, get_CITY_DATA_PATH


if __name__ == '__main__':

    CITY_DATA_PATH = get_CITY_DATA_PATH()
    setupLogging ('log/learning/manuallyFilterDb.log', logging.INFO, 'a')

    db_in_path = op.join (CITY_DATA_PATH, 'datasets/sparse/Databases/572-Oct28-10h/color-ds2.5-dp12.0-to903.db')
    db_out_path = op.join (CITY_DATA_PATH, 'datasets/sparse/Databases/572-Oct28-10h/color-ds2.5-dp12.0.db')

    params = { 'imagefile_start': 'datasets/sparse/Images/572-Oct28-10h/000903.jpg' }
    #params = { 'car_condition': 'AND name = "vehicle"' }
    #params = {}

    #processing.dbClassifyName (db_in_path, db_out_path, params)
    processing.dbClassifyColor (db_in_path, db_out_path, params)
    #processing.dbExamine (db_in_path)
    
