import logging
import sys
import os, os.path as op
sys.path.insert(0, os.path.abspath('..'))
from processing import dbMerge
from utilities import setupLogging


if __name__ == '__main__':

    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        raise Exception ('Set environmental variables CITY_PATH, CITY_DATA_PATH')

    setupLogging ('log/learning/dbMerge.log', logging.INFO, 'a')

    CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')
    db_in_paths = []
    db_in_paths.append( op.join (CITY_DATA_PATH, 'datasets/sparse/Databases/572-Oct28-10h/clas-ds2.5-dp12.0.db') )
    db_in_paths.append( op.join (CITY_DATA_PATH, 'datasets/sparse/Databases/578-Mar15-10h/clas-ds2.5-dp12.0.db') )
    db_out_path = op.join (CITY_DATA_PATH, 'databases/sparse-to-Mar18.db')

    dbMerge (db_in_paths, db_out_path)
    