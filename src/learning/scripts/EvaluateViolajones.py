import logging
import os, sys
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../violajones'))
from setupHelper import setupLogging
import evaluateTask


setupLogging ('log/detector/runTestTask.log', logging.INFO, 'a')

task_path = 'learning/violajones/tasks/Apr02-adaptive.json'
db_eval_path = 'datasets/labelme/Databases/572/distinct-frames.db'
result_path = os.path.join('learning/violajones/models', 
                           os.path.splitext(os.path.basename(task_path))[0], 'eval-d0.7.txt')

params = { 'debug_show': False,
           'show_experiments': False,
           'result_path': result_path,
           'dist_thresh': 0.7
           #'model': '40x30-e0.1-circle'
         }

evaluateTask.evaluateTask (task_path, db_eval_path, params)
