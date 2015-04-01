import logging
import os, sys
sys.path.insert(0, os.path.abspath('..'))
from setupHelper import setupLogging
import processing


setupLogging ('log/learning/manuallyFilterDb.log', logging.INFO, 'a')

db_in_path  = 'datasets/sparse/Databases/671-Mar24-12h/color-ds2.5-dp12.0.db'
db_out_path = 'datasets/sparse/Databases/671-Mar24-12h/prune-ds2.5-dp12.0.db'

params = {}
params = { 'imagefile_start': 'datasets/sparse/Images/671-Mar24-12h/000665.jpg' }
#params = { 'car_condition': 'name = "taxi"' }

processing.dbClassifyName (db_in_path, db_out_path, params)
#processing.dbClassifyColor (db_in_path, db_out_path, params)
#processing.dbExamine (db_in_path, params)

