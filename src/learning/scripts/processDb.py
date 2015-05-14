import logging
import sys, os
sys.path.insert(0, os.path.abspath('..'))
import processing
sys.path.insert(0, os.path.abspath('../labelme'))
import labelme2db
from setupHelper import setupLogging
import fnmatch



setupLogging ('log/learning/ProcessDb.log', logging.WARNING, 'a')

in_dir = os.path.join(os.getenv('CITY_DATA_PATH'), 'datasets/labelme/Databases/572-Oct30-17h-pair')

#params = { }
#params = { 'images_dir': 'datasets/labelme/Images/572-Oct30-17h-frame',
#           'ghosts_dir': 'datasets/labelme/Ghosts/572-Oct30-17h-frame',
#           'masks_dir':  'datasets/labelme/Masks/572-Oct30-17h-frame' }

#db_in_paths = []
#for root, dirnames, filenames in os.walk(in_dir):
#    for filename in fnmatch.filter(filenames, '*.db'):
#        db_in_paths.append(os.path.join(root, filename))
#
#for db_in_path in db_in_paths:
#    try:
#        processing.dbCustomScript (db_in_path, None, params)
#    except Exception,e: print (db_in_path, str(e))


db_in_path  = 'datasets/labelme/Databases/572-Oct30-17h-pair/vj1-and-fromback.db'
db_out_path = 'datasets/labelme/Databases/572-Oct30-17h-pair/vj1-and-fromback-thres.db'

#params = {'score_map_path': 'models/cam572/mapFromback.tiff',
#          'debug_show': True,
#          'border_thresh_perc': -0.01,
#          'min_width_thresh': 5,
#          'size_acceptance': 3,
#          'ratio_acceptance': 3
#          }
#processing.dbMaskScores (db_in_path, db_out_path, params)


params = {'size_map_path': 'models/cam572/mapSize.tiff',
          'debug_show': False,
          'border_thresh_perc': 0.01,
          'min_width_thresh': 5,
          'size_acceptance': 2,
          'ratio_acceptance': 3
          }
#processing.dbFilter (db_in_path, db_out_path, params)


#params = {'expand_perc': 0.3,
#          'debug_show': True }

#processing.dbExpandBboxes (db_in_path, db_out_path, params)

processing.dbThresholdScore (db_in_path, db_out_path, params)
