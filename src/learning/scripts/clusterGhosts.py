import logging
import os, sys
sys.path.insert(0, os.path.abspath('..'))
from setupHelper import setupLogging
import clustering


setupLogging ('log/learning/clusterGhosts.log', logging.INFO, 'a')

in_db_path   = 'databases/wr-e0.3.db'
filters_path = 'clustering/filters/angles.json'
out_dir      = 'clustering/test'

clustering.collectGhostsTask (in_db_path, filters_path, out_dir)
