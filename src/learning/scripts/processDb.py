import logging, logging.handlers
import sys
import os, os.path as op
sys.path.insert(0, os.path.abspath('..'))
from processing import Processor


if __name__ == '__main__':

    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        raise Exception ('Set environmental variables CITY_PATH, CITY_DATA_PATH')

    log = logging.getLogger('')
    log.setLevel (logging.WARNING)
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s: \t%(message)s')
    log_path = op.join (os.getenv('CITY_PATH'), 'log/learning/labelme/process.log')
    fh = logging.handlers.RotatingFileHandler(log_path, mode='w')
    fh.setFormatter(formatter)
    log.addHandler(fh)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    log.addHandler(sh)
 

    CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')
    db_in_path  = op.join (CITY_DATA_PATH, 'labelme/Databases/src-all.db')
    db_out_path = op.join (CITY_DATA_PATH, 'databases/w-ratio.db')

    params = {'geom_maps_dir': op.join (CITY_DATA_PATH, 'models/cam572/'),
              'debug_show': False,
              'keep_ratio': True,
              'border_thresh_perc': -0.01 }

    processor = Processor (params)
    processor.processDb (db_in_path, db_out_path)
    