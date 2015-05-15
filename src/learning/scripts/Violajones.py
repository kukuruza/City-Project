import logging
import sys, os
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning/violajones'))
import processing
from setupHelper import setupLogging
from dbViolajones import detectViolajonesTask

setupLogging ('log/learning/Violajones.log', logging.INFO, 'a')
  
db_in_path = 'datasets/labelme/Databases/572-Nov28-10h-pair/init.db'
db_out_dir = 'datasets/labelme/Databases/572-Nov28-10h-pair/detected'
task_path = 'learning/violajones/tasks/May07-chosen.json'
db_true_path = 'datasets/labelme/Databases/572-Nov28-10h-pair/parsed.db'

detectViolajonesTask (db_in_path, task_path, db_out_dir, { 'debug_show': False })
#dbEvaluateTask (task_path, db_true_path, db_in_path, params)
