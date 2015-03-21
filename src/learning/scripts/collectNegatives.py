import logging
import sys
import os, os.path as op
sys.path.insert(0, os.path.abspath('..'))
import negatives
from utilities import setupLogging, get_CITY_DATA_PATH


if __name__ == '__main__':

    CITY_DATA_PATH = get_CITY_DATA_PATH()
    setupLogging ('log/learning/collectNegatives.log', logging.INFO)

    db_path      = op.join (CITY_DATA_PATH, 'datasets/labelme/Databases/src-frames.db')
    filters_path = op.join (CITY_DATA_PATH, 'clustering/filters/neg_24x18_car.json')
    out_dir      = op.join (CITY_DATA_PATH, 'clustering/neg_car_masked')

    params = { 'spot_scale': 0.7,
               'method': 'mask',
               'dilate': 0.25,
               'erode': 0.4 }

    negatives.negativeGrayspots (db_path, filters_path, out_dir, params)
