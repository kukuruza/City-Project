import logging
import os, sys
sys.path.insert(0, os.path.abspath('..'))
from setupHelper import setupLogging
import processing


setupLogging ('log/learning/manuallyFilterDb.log', logging.INFO, 'a')

db_in_path =  'datasets/sparse/Databases/119-Apr09-13h/clas.db'
db_out_path = 'datasets/sparse/Databases/119-Apr09-13h/color.db'

params = {}
#params['car_constraint'] = 'name = "limo"'
#params['imagefile_start'] = 'datasets/sparse/Images/119-Apr09-13h/000035.jpg'
params['disp_scale'] = 3

#processing.dbClassifyName (db_in_path, db_out_path, params)
processing.dbClassifyColor (db_in_path, db_out_path, params)
#processing.dbExamine (db_in_path, params)

