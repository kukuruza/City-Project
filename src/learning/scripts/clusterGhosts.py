import logging
import os, sys
sys.path.insert(0, os.path.abspath('..'))
from utilities import setupLogging
import clustering


setupLogging ('log/learning/clusterGhosts.log', logging.INFO, 'a')

in_db_path   = 'databases/sparse-wb-wr-e0.1.db'
filters_path = 'clustering/filters/name.json'
out_dir      = 'clustering/name-sparse-e0.1'

clustering.collectGhosts (in_db_path, filters_path, out_dir)
