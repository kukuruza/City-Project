import os, sys, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import logging
from learning.helperSetup import setupLogging, dbInit, atcity
from learning.dbExtractFeatures import extractFeatures


''' demo to write features to a particular database '''

setupLogging ('log/detector/fasterRcnn/extractFeatures.log', logging.INFO, 'a')

# input
db_file = 'data/databases/labelme/572-Oct30-17h-pair/parsed-e0.1-image.db'
out_file = 'data/counting/features/572-Oct30-17h-pair/parsed-e0.1-image-vgg-fc7.txt'
params = {'model_dir': 'vgg16', 'features_layer': 'fc7'}

(conn, cursor) = dbInit (atcity(db_file))
extractFeatures (cursor, out_file, params)
conn.close()
