import logging, logging.handlers
import sys
import os, os.path as op
sys.path.insert(0, os.path.abspath('..'))
from clustering import Clusterer


if __name__ == '__main__':

    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        raise Exception ('Set environmental variables CITY_PATH, CITY_DATA_PATH')

    log = logging.getLogger('')
    log.setLevel (logging.WARNING)
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s: \t%(message)s')
    log_path = op.join (os.getenv('CITY_PATH'), 'log/learning/labelme/analyzeFrames.log')
    fh = logging.handlers.RotatingFileHandler(log_path, mode='w')
    fh.setFormatter(formatter)
    log.addHandler(fh)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    log.addHandler(sh)


    CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')

    clusterer = Clusterer()
    clusterer.collectGhosts (op.join (CITY_DATA_PATH, 'databases/w-ratio.db'),
                             op.join (CITY_DATA_PATH, 'clustering/cars_by_size/clusters.json'), 
                             op.join (CITY_DATA_PATH, 'clustering/cars_by_size'))

