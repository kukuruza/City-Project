import logging
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
from setupHelper import setupLogging
from dbAll import Processor


setupLogging ('log/learning/Manually.log', logging.INFO, 'a')

db_vj_distant = 'datasets/labelme/Databases/572-Nov28-10h-pair/detected-vj-distant/mhr0.995-mfar0.7-wtr0.95.db'
db_vj_close   = 'datasets/labelme/Databases/572-Nov28-10h-pair/detected-vj-close/mhr0.995-mfar0.7-wtr0.95.db'
db_fromback   = 'datasets/labelme/Databases/572-Nov28-10h-pair/detected/fromback-dr8.db'
db_out_path   = 'datasets/labelme/Databases/572-Nov28-10h-pair/detected/all-3.db'

Processor(db_fromback, db_fromback + '-tmp')\
    .maskScores ({'score_map_path': 'models/cam572/mapFromback.tiff'})\
    .commit()

Processor(db_vj_distant, db_vj_distant + '-tmp')\
    .maskScores ({'score_map_path': 'models/cam572/mapVjDistant-nhor.tiff'})\
    .commit()

# do apply a mask to db_vj_distant
#Processor(db_vj_distant, db_vj_close + '-tmp')\
#    .maskScores ({'score_map_path': 'models/cam572/mapVjClose.tiff'})\
#    .show()\
#    .commit()

Processor(db_vj_distant + '-tmp', db_out_path)\
    .merge (db_fromback + '-tmp')\
    .merge (db_vj_close)\
    .filterSize ( {'size_map_path': 'models/cam572/mapSize.tiff', 'debug_show': False } )\
    .thresholdScore ({'threshold': 0.7, 'debug_show': False } )\
    .clusterBboxes ({'threshold': 0.7, 'debug_show': False})\
    .show()\
    .commit()



