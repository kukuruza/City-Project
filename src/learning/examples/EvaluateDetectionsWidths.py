#! /usr/bin/env python
import os, sys, os.path as op
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup import setupLogging, dbInit, atcity
from learning.dbEvaluate  import dbEvalClass
from learning.dbModify import filterCustom
import matplotlib.pyplot as plt



parser = argparse.ArgumentParser()
parser.add_argument('--true_db_file', required=True)
parser.add_argument('--eval_db_file', required=True)
parser.add_argument('--logging_level', default=20, type=int)
parser.add_argument('--car_constraints', required=True, nargs='+',
        help='''e.g.: 'width >= 25' ''')
args = parser.parse_args()

setupLogging ('log/learning/EvaluateDetectionsWidth.log', args.logging_level, 'a')


f = open(atcity(op.join(op.dirname(args.eval_db_file), 'results.txt')), 'w')

for car_constraint in args.car_constraints:

  (conn_true, cursor_true) = dbInit(args.true_db_file, backup=False)
  (conn_eval, cursor_eval) = dbInit(args.eval_db_file, backup=False)

  params = {'car_constraint': car_constraint}
  rec, prec, ap = dbEvalClass (c_gt=cursor_true, c_det=cursor_eval, params=params)
  print 'car_constraint: %s, ap: %0.3f' % (car_constraint, ap)
  f.write('car_constraint: %s, ap: %0.3f\n' % (car_constraint, ap))

  suffix = car_constraint.replace(" ", "").replace(">", "").replace("=", "")
  ax = plt.subplot(111)
  plt.plot(rec, prec)
  plt.xlabel('recall')
  plt.ylabel('precision')
  #plt.title('labelled frames')
  ax.set_xlim([0,1])
  ax.set_ylim([0,1])
  plt.grid(True)
  dir_path = atcity(op.join(op.dirname(args.eval_db_file), 'ROC'))
  if not op.exists(dir_path):
    os.makedirs(dir_path)
  plt.savefig(atcity(op.join(dir_path, 'ROC-%s.png' % suffix)))
  plt.close()

  conn_eval.close()
  conn_true.close()

f.close()

