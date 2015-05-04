import logging
import os, sys
sys.path.insert(0, os.path.abspath('..'))
from setupHelper import setupLogging
sys.path.insert(0, os.path.abspath('../labelme'))
import labelme2db


setupLogging ('log/learning/Labelme2dbFrames.log', logging.INFO, 'a')

db_in_path  = 'datasets/labelme/Databases/572-Oct30-17h-frame/init.db'
db_out_path = 'datasets/labelme/Databases/572-Oct30-17h-frame/parsed.db'

params = { 'debug_show': False }

labelme2db.folder2frames (db_in_path, db_out_path, params)
