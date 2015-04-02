import logging
import os, sys
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../violajones'))
from setupHelper import setupLogging
import evaluateTask


setupLogging ('log/detector/runTestTask.log', logging.DEBUG, 'a')

task_path = 'learning/violajones/tasks/Apr02-ex-er-di.json'
db_eval_path = 'datasets/labelme/Databases/572/distinct-frames.db'

params = { 'debug_show': True,
           'show_experiments': False 
         }

evaluateTask.evaluateTask (task_path, db_eval_path, params)
