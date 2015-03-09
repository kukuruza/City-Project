#!/bin/python
#
# This script collects negative training samples from images
# It uses clusters.json file for information about filters
#
# Assumptions are: 1) all cars are labelled in each image (maybe several times)
#


import logging, logging.handlers
import sys
import os, os.path as op
sys.path.insert(0, os.path.abspath('..'))
from negatives import NegativesGrayspots


if __name__ == '__main__':

    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        raise Exception ('Set environmental variables CITY_PATH, CITY_DATA_PATH')

    log = logging.getLogger('')
    log.setLevel (logging.INFO)
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s: \t%(message)s')
    log_path = op.join (os.getenv('CITY_PATH'), 'log/learning/collectNegatives.log')
    fh = logging.handlers.RotatingFileHandler(log_path, mode='w')
    fh.setFormatter(formatter)
    log.addHandler(fh)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    log.addHandler(sh)
 

    CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')
    db_path      = op.join (CITY_DATA_PATH, 'labelme/Databases/src-all.db')
    out_dir      = op.join (CITY_DATA_PATH, 'clustering/neg_by_type')
    filters_path = op.join (out_dir, 'clusters.json')

    processor = NegativesGrayspots ()
    processor.processDb (db_path, filters_path, out_dir)
