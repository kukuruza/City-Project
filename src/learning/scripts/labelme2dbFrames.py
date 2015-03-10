#
# wrapper around folder2frames
# set up logging, paths, and call the function
#

import logging
import sys
import os, os.path as op
sys.path.insert(0, os.path.abspath('../labelme'))
from labelme2db import folder2frames
from utilities import setupLogging


if __name__ == '__main__':

    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        raise Exception ('Set environmental variables CITY_PATH, CITY_DATA_PATH')

    setupLogging ('log/learning/analyzeFrames.log', logging.INFO)

    folder = 'cam572-bright-frames'
    db_path = op.join (os.getenv('CITY_DATA_PATH'), 'labelme/Databases/src-all.db')

    params = { 'backimage_file': 'camdata/cam572/5pm/models/backimage.png',
               'debug_show': False }

    folder2frames (folder, db_path, params)
    