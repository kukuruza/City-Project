import logging
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
import dbCnn
import helperSetup
import helperImg


helperSetup.setupLogging ('log/learning/ClassifyCnn.log', logging.INFO, 'a')

db_in_path  = 'datasets/labelme/Databases/572-Nov28-10h-pair/parsed-e0.1.db'
db_out_path = 'datasets/labelme/Databases/572-Nov28-10h-pair/classify-cnn/parsed-e0.1.db'

network_path = 'cnn/architectures/vehicle-deploy-py.prototxt'
model_path   = 'cnn/models/vehicle_iter_20000.caffemodel'

(conn, cursor) = helperSetup.dbInit(db_in_path, db_out_path)
dbCnn = dbCnn.DbCnn(network_path, model_path)
dbCnn.classify (cursor, {'label_dict': {0: 'negative', 1: 'vehicle'}, 'resize': (40, 30)})
conn.commit()
conn.close()
