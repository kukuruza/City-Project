import logging
import os, sys
sys.path.insert(0, os.path.abspath('..'))
from setup_helper import setupLogging
import clustering


setupLogging ('log/learning/writeInfoFile.log', logging.INFO, 'a')

in_db_path   = 'databases/sparse-Mar18-wb-wr-ex0.3.db'
filters_path = 'clustering/filters/byname_24x18.json'
out_dir      = 'learning/violajones/byname_24x18-2'

clustering.writeInfoFile (in_db_path, filters_path, out_dir)
