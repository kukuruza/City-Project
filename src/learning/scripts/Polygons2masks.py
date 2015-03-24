import logging
import sys
import os, os.path as op
sys.path.insert(0, os.path.abspath('..'))
from utilities import setupLogging, get_CITY_DATA_PATH
import processing


if __name__ == '__main__':

    CITY_DATA_PATH = get_CITY_DATA_PATH()
    setupLogging ('log/learning/clusterGhosts.log', logging.INFO)

    db_in_path = op.join (CITY_DATA_PATH, 'datasets/labelme/Databases/src-frames-2.db')

    in_db_path   = op.join (CITY_DATA_PATH, 'databases/sparse-Mar18-wb-wr-ex0.3.db')
    filters_path = op.join (CITY_DATA_PATH, 'clustering/filters/byname_24x18.json')
    out_dir      = op.join (CITY_DATA_PATH, 'clustering/sparse-byname_24x18-2')

    processing.dbPolygonsToMasks (in_db_path, filters_path)

