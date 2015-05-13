import logging
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning/cnn'))
from setupHelper import setupLogging
import cnnImport


setupLogging ('log/learning/ImportCnnLabels.log', logging.INFO, 'a')

db_in_path  = 'learning/violajones/eval/May07-chosen/ex0.1-noise1.5-pxl5.db'
db_out_path = 'learning/violajones/eval/May07-chosen/ex0.1-noise1.5-pxl5-cnn.db'
labels_path = 'cnn/predictions/572-Oct30-17h-pair/predVJ-e0.1-noise1.5-pxl5.txt'

cnnImport.dbImportLabels (db_in_path, db_out_path, labels_path, { })

