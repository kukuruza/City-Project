import logging
import os, sys
sys.path.insert(0, os.path.abspath('../labelme'))
from utilities import setupLogging
import labelme2db


setupLogging ('log/learning/analyzePairs.log', logging.INFO, 'a')

folder = 'cam572-5pm-pairs'
db_path = 'datasets/labelme/Databases/src-pairs-2.db'

params = { 'backimage_file': 'camdata/cam572/5pm/models/backimageTwice.png',
           'labelme_dir': 'datasets' 
         }

labelme2db.folder2pairs (folder, db_path, params)
