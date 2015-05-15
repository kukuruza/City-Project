import logging
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
from setupHelper import setupLogging
from dbBase import Processor


setupLogging ('log/learning/ImportCnnLabels.log', logging.INFO, 'a')

db_in_path  = 'learning/violajones/eval/May07-chosen/mhr0.995-mfar0.7-wtr0.95.db'
db_out_path = 'learning/violajones/eval/May07-chosen/test.db'
labels_path = 'cnn/predictions/572-Oct30-17h-pair/mhr0.995-mfar0.7-wtr0.95-e0.1.txt'

Processor(db_in_path, db_out_path)\
    .importLabels (labels_path, { })\
    .show()\
    .commit()

