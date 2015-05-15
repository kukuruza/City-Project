import logging
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning/labelme'))
from setupHelper import setupLogging
import labelme2db
 

setupLogging ('log/learning/Labelme2dbPairs.log', logging.INFO, 'a')

db_in_path  = 'datasets/labelme/Databases/572-Nov28-10h-pair/init.db'
db_out_path = 'datasets/labelme/Databases/572-Nov28-10h-pair/parsed.db'

params = { 'debug_show': False }

labelme2db.folder2pairs (db_in_path, db_out_path, params)
