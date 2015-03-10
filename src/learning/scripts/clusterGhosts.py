#
# wrapper around Clusterer.collectGhosts()
# set up logging, paths, and call the function, and write a readme
#

import logging
import sys
import os, os.path as op
sys.path.insert(0, os.path.abspath('..'))
from clustering import Clusterer
from utilities import setupLogging


if __name__ == '__main__':

    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        raise Exception ('Set environmental variables CITY_PATH, CITY_DATA_PATH')
    CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')

    setupLogging ('log/learning/clusterGhosts.log', logging.INFO)

    in_db_path   = op.join (CITY_DATA_PATH, 'databases/w-ratio.db')
    filters_path = op.join (CITY_DATA_PATH, 'clustering/filters/cars_bysize.json')
    out_dir      = op.join (CITY_DATA_PATH, 'clustering/cars_bysize')

    clusterer = Clusterer()
    clusterer.collectGhosts (in_db_path, filters_path, out_dir)

    with open(op.join(out_dir, 'readme.txt'), 'w') as readme:
        readme.write('from database ' + in_db_path + '\n')
        readme.write('with filters  ' + filters_path + '\n')

