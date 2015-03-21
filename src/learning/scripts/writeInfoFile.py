import logging
import sys
import os, os.path as op
sys.path.insert(0, os.path.abspath('..'))
import clustering
from utilities import setupLogging, get_CITY_DATA_PATH


if __name__ == '__main__':

    setupLogging ('log/learning/writeInfoFile.log', logging.INFO, 'a')

    in_db_path   = op.join (get_CITY_DATA_PATH(), 'databases/sparse-Mar18-wb-wr-ex0.3.db')
    filters_path = op.join (get_CITY_DATA_PATH(), 'clustering/filters/byname_24x18.json')
    out_dir      = op.join (get_CITY_DATA_PATH(), 'learning/violajones/byname_24x18-2')

    clustering.writeInfoFile (in_db_path, filters_path, out_dir)

