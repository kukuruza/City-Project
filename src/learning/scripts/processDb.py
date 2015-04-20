import logging
import sys, os
sys.path.insert(0, os.path.abspath('..'))
import processing
from setupHelper import setupLogging


setupLogging ('log/learning/processDb.log', logging.INFO, 'a')

#db_in_path  = 'datasets/sparse/Databases/119-Apr09-13h/color.db'
#db_out_path = 'datasets/sparse/Databases/119-Apr09-13h/angles.db'


# needs params
#params = {'size_map_path':  'models/cam119/mapSize.tiff',
#          'yaw_map_path':   'models/cam119/mapYaw.tiff',
#          'pitch_map_path': 'models/cam119/mapPitch.tiff'}
#processing.dbAssignOrientations (db_in_path, db_out_path, params)


#params = {'size_map_path': 'models/cam717/mapSize.tiff',
#          'debug_show': False,
#          'border_thresh_perc': -0.01,
#          'min_width_thresh': 5,
#          'size_acceptance': (0.3, 2)
#          }
#processing.dbFilter (db_in_path, db_out_path, params)



db_in_path  = 'databases/all.db'
db_out_path = 'databases/wr-e0.3.db'


params = {'debug_show': True,
          'keep_ratio': True,
          'expand_perc': 0.3 }
processing.dbExpandBboxes (db_in_path, db_out_path, params)


#processing.dbCustomScript (db_in_path, db_out_path)


#params = { 'masks_dir': 'datasets/sparse/Masks/572-Oct28-10h/' }
#processing.dbMove (db_in_path, db_out_path, params)
