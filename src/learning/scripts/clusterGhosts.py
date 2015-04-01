import logging
import os, sys
sys.path.insert(0, os.path.abspath('..'))
from setupHelper import setupLogging
import clustering


setupLogging ('log/learning/clusterGhosts.log', logging.INFO, 'a')

in_db_path   = 'databases/sp-color-wr-e0.3.db'
filters_path = 'clustering/filters/color.json'
out_dir      = 'clustering/color-572-Oct28-10h'

clustering.collectGhosts (in_db_path, filters_path, out_dir)
