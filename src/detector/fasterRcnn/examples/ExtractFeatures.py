import logging
import os, sys, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/detector/fasterRcnn'))
from helperSetup import setupLogging, dbInit
from dbExtractFeatures import extractFeatures


''' demo to write features to a particular database '''

setupLogging ('log/detector/fasterRcnn/extractFeatures.log', logging.INFO, 'a')

# input
db_path = 'databases/labelme/572-Oct30-17h-pair/parsed-e0.1-image.db'
out_path = 'counting/features/572-Oct30-17h-pair/parsed-e0.1-image-vgg-fc7.txt'
params = {'model_dir': 'vgg16', 'features_layer': 'fc7'}

(conn, cursor) = dbInit (op.join(os.getenv('CITY_DATA_PATH'), db_path))
extractFeatures (cursor, out_path, params)
conn.close()
