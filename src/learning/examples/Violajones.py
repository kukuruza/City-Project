import logging
import sys, os
from learning.helperSetup  import setupLogging
from learning.dbViolajones import detectViolajonesTask
from learning.dbEvaluate   import dbEvaluateTask

setupLogging ('log/learning/Violajones.log', logging.INFO, 'a')
  
db_in_file = 'datasets/labelme/Databases/572-Nov28-10h-pair/init.db'
db_out_dir = 'datasets/labelme/Databases/572-Nov28-10h-pair/detected-close'
task_file = 'learning/violajones/tasks/May17-high-yaw.json'
db_true_file = 'datasets/labelme/Databases/572-Nov28-10h-pair/parsed.db'

detectViolajonesTask (db_in_file, task_file, db_out_dir, { 'debug_show': False })
#dbEvaluateTask (task_file, db_true_file, db_in_file, params)
