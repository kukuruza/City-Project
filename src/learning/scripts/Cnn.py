import logging
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
from setupHelper import setupLogging
from dbCnn import CnnProcessor


setupLogging ('log/learning/ImportCnnLabels.log', logging.INFO, 'a')

db_in_path  = 'learning/violajones/eval/May07-chosen/mhr0.995-mfar0.7-wtr0.95.db'
db_out_path = 'learning/violajones/eval/May07-chosen/test.db'

network_path = os.path.join(os.getenv('CITY_DATA_PATH'), 'cnn/prototxt-files/deploy_python.prototxt')
model_path   = os.path.join(os.getenv('CITY_DATA_PATH'), 'cnn/models/city_quick_iter_4000.caffemodel')
params = {'network_path': network_path, 'model_path': model_path}

CnnProcessor(db_in_path, db_out_path, params)\
    .classifyDb ({'resize': [40, 30]})\
    .commit()

