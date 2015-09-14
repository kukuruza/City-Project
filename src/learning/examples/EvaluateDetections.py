import logging
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
import helperSetup
import dbEvaluate


helperSetup.setupLogging ('log/detector/EvaluateDetections.log', logging.INFO, 'a')

db_eval_path = 'candidates/572-Oct30-17h-pair_sizemap.db'
db_true_path = 'datasets/labelme/Databases/572-Oct30-17h-pair/parsed-e0.1.db'

params = { 'debug': True,
           'dist_thresh': 0.0
         }

(conn_eval, cursor_eval) = helperSetup.dbInit(os.path.join(os.getenv('CITY_DATA_PATH'), db_eval_path))
(conn_true, cursor_true) = helperSetup.dbInit(os.path.join(os.getenv('CITY_DATA_PATH'), db_true_path))

dbEvaluate.evaluateDetector (cursor_eval, cursor_true, params)

conn_eval.close()
conn_true.close()
