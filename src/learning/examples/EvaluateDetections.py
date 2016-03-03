import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
from learning.helperSetup import setupLogging, dbInit, atcity
from learning.dbEvaluate  import evaluateDetector


setupLogging ('log/detector/EvaluateDetections.log', logging.INFO, 'a')

db_eval_file = 'candidates/572-Oct30-17h-pair_sizemap.db'
db_true_file = 'databases/labelme/572-Oct30-17h-pair/parsed-e0.1.db'

params = { 'debug': True,
           'dist_thresh': 0.7
         }

(conn_eval, cursor_eval) = dbInit(db_eval_file)
(conn_true, cursor_true) = dbInit(db_true_file)

evaluateDetector (cursor_eval, cursor_true, params)

conn_eval.close()
conn_true.close()
