import logging
import os, sys
sys.path.insert(0, os.path.abspath('..'))
from setup_helper import setupLogging
import processing


setupLogging ('log/learning/manuallyFilterDb.log', logging.INFO, 'a')

db_in_path = 'datasets/sparse/Databases/578-Jan22-14h/clas-ds2.5-dp12.0-satwik.db'
db_out_path = 'datasets/sparse/Databases/578-Jan22-14h/clas-ds2.5-dp12.0-satwik.db'

#params = { 'imagefile_start': 'datasets/sparse/Images/578-Mar15-10h/000559.jpg' }
params = {'car_condition':'AND name = "taxi"'};
#params = { 'imagefile_start': 'datasets/sparse/Images/578-Jan22-14h/000071.jpg' }
#params = { 'imagefile_start': 'datasets/sparse/Images/671-Mar24-12h/000665.jpg' }
#params = { 'car_condition': 'AND name = "vehicle"' }
#params = {}

processing.dbClassifyName (db_in_path, db_out_path, params)
#processing.dbClassifyColor (db_in_path, db_out_path, params)
#processing.dbExamine (db_in_path)

