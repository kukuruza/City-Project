# Parse labelme vstacked images into car-matches between frames
#
# Script takes a 'folder' name. 
# /Images/folder and /Annotations/folder are the results of the labelme,
#   Each image is two vertically stacked frames
#   Labelme annotations signify matches between frames
#
# The output is a number of files with names like f000-001-N.mat, 
#   which keeps the match of car N between frames 0 and 1 as {car1, car2}
#

import logging, logging.handlers
import sys
import os, os.path as op
sys.path.insert(0, os.path.abspath('../labelme'))
from labelme2db import folder2pairs


if __name__ == '__main__':

    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        raise Exception ('Set environmental variables CITY_PATH, CITY_DATA_PATH')

    log = logging.getLogger('')
    log.setLevel (logging.WARNING)
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s: \t%(message)s')
    log_path = op.join (os.getenv('CITY_PATH'), 'log/learning/labelme/analyzePairs.log')
    fh = logging.handlers.RotatingFileHandler(log_path, mode='w')
    fh.setFormatter(formatter)
    log.addHandler(fh)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    log.addHandler(sh)

    folder = 'cam572-5pm-pairs'
    db_path = op.join(os.getenv('CITY_DATA_PATH'), 'labelme/Databases/src-pairs.db')

    params = { 'backimage_file': 'camdata/cam572/5pm/models/backimageTwice.png' }

    folder2pairs (folder, db_path, params)
