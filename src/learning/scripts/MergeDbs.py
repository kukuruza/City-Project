import logging
import os, sys
sys.path.insert(0, os.path.abspath('..'))
from utilities import setupLogging
import processing


setupLogging ('log/learning/dbMerge.log', logging.INFO, 'a')

db_in_paths = []
db_in_paths.append( 'datasets/sparse/Databases/572-Oct28-10h/clas-ds2.5-dp12.0.db')
db_in_paths.append( 'datasets/sparse/Databases/578-Mar15-10h/clas-ds2.5-dp12.0.db')
db_in_paths.append( 'datasets/sparse/Databases/671-Mar24-12h/clas-ds2.5-dp12.0-to665.db')
db_out_path = 'databases/sparse.db')

processing.dbMerge (db_in_paths, db_out_path)
