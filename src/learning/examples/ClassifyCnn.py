import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
from learning.helperSetup import setupLogging, dbInit
from learning.dbCnn       import DbCnn


setupLogging ('log/learning/ClassifyCnn.log', logging.INFO, 'a')

db_in_file  = 'databases/labelme/572-Nov28-10h-pair/parsed-e0.1.db'
db_out_file = 'databases/labelme/572-Nov28-10h-pair/classify-cnn/parsed-e0.1.db'

network_file = 'cnn/architectures/vehicle-deploy-py.prototxt'
model_file   = 'cnn/models/vehicle_iter_20000.caffemodel'

(conn, cursor) = dbInit(db_in_file, db_out_file)
dbCnn = DbCnn(network_file, model_file)
dbCnn.classify(cursor, {'label_dict': {0: 'negative', 1: 'vehicle'}, 'resize': (40, 30)})
conn.commit()
conn.close()
