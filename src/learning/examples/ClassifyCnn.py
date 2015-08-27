import logging
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
import helperSetup
from dbCnn import CnnClassifier


helperSetup.setupLogging ('log/learning/ClassifyCnn.log', logging.INFO, 'a')

db_in_path  = 'learning/violajones/eval/May07-chosen/mhr0.995-mfar0.7-wtr0.95.db'
db_out_path = 'learning/violajones/eval/May07-chosen/test.db'

network_path = 'cnn/prototxt-files/deploy_python.prototxt'
model_path   = 'cnn/models/city_quick_iter_4000.caffemodel'

(conn, cursor) = helperSetup.dbInit(db_in_path, db_out_path)
CnnClassifier (network_path, model_path).classifyDb (cursor, {'resize': [40, 30]})
conn.commit()
conn.close()
