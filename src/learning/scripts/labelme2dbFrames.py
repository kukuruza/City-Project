import logging, logging.handlers
import sys
import os, os.path as op
sys.path.insert(0, os.path.abspath('../labelme'))
from labelme2db import folder2frames


if __name__ == '__main__':

    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        raise Exception ('Set environmental variables CITY_PATH, CITY_DATA_PATH')

    log = logging.getLogger('')
    log.setLevel (logging.INFO)
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s: \t%(message)s')
    log_path = op.join (os.getenv('CITY_PATH'), 'log/learning/labelme/analyzeFrames.log')
    fh = logging.handlers.RotatingFileHandler(log_path, mode='w')
    fh.setFormatter(formatter)
    log.addHandler(fh)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    log.addHandler(sh)


    folder = 'cam572-bright-frames'
    db_path = op.join (os.getenv('CITY_DATA_PATH'), 'labelme/Databases/src-all.db')

    params = { 'backimage_file': 'camdata/cam572/5pm/models/backimage.png',
               'debug_show': False }

    folder2frames (folder, db_path, params)
    