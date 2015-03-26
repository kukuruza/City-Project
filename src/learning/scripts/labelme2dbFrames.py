import logging
import os, sys
sys.path.insert(0, os.path.abspath('../labelme'))
from setup_helper import setupLogging
import labelme2db


setupLogging ('log/learning/analyzeFrames.log', logging.INFO, 'a')

folder = 'cam572-bright-frames'
db_path = 'datasets/labelme/Databases/src-frames-2.db'

params = { 'backimage_file': 'camdata/cam572/5pm/models/backimage.png',
           'labelme_dir': 'datasets',
           'debug_show': False }

labelme2db.folder2frames (folder, db_path, params)
