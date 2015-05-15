import logging
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning/labelme'))
from setupHelper import setupLogging
import labelme2db


setupLogging ('log/learning/Labelme2dbFrames.log', logging.INFO, 'a')

db_in_path  = 'datasets/labelme/Databases/572-Oct30-17h-frame/init.db'
db_out_path = 'datasets/labelme/Databases/572-Oct30-17h-frame/parsed.db'

params = { 'debug_show': False }

labelme2db.folder2frames (db_in_path, db_out_path, params)
