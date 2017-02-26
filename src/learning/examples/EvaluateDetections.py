import os, sys, os.path as op
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup import setupLogging, dbInit, atcity
from learning.dbEvaluate  import evalClass, evalCounting
from learning.dbModify import filterCustom
import matplotlib.pyplot as plt



parser = argparse.ArgumentParser()
parser.add_argument('--true_db_file', required=True)
parser.add_argument('--eval_db_file', required=True)
parser.add_argument('--logging_level', default=20, type=int)
parser.add_argument('--car_constraint', required=False,
        help='''e.g.: 'width >= 25' ''',
        default='1')
args = parser.parse_args()

setupLogging ('log/learning/EvaluateDetections.log', args.logging_level, 'a')


(conn_true, cursor_true) = dbInit(args.true_db_file, backup=False)
(conn_eval, cursor_eval) = dbInit(args.eval_db_file, backup=False)

params = {'car_constraint': args.car_constraint}
rec, prec, ap = evalClass (c_gt=cursor_true, c_det=cursor_eval, params=params)
#det_counts, gt_counts = evalCounting (c_gt=cursor_true, c_det=cursor_eval)

conn_eval.close()
conn_true.close()

suffix = str(params['car_constraint']).replace(" ", "").replace(">", "").replace("=", "")

print 'recall:', rec
print 'precision:', prec
print 'ap: %0.3f' % ap
ax = plt.subplot(111)
plt.plot(rec, prec)
plt.xlabel('recall')
plt.ylabel('precision')
#plt.title('labelled frames')
ax.set_xlim([0,1])
ax.set_ylim([0,1])
plt.grid(True)
plt.savefig(atcity(op.join(op.dirname(args.eval_db_file), 'ROC-%s.png' % suffix)))
plt.close()

# t = range(len(det_counts))
# ax = plt.subplot(111)
# plt.plot(t, det_counts, 'r')
# plt.plot(t, gt_counts, 'b')
# plt.xlabel('frame id')
# plt.ylabel('count')
# #plt.title('labelled frames')
# # ax.set_xlim([0,1])
# # ax.set_ylim([0,1])
# plt.grid(True)
# plt.savefig(atcity(op.join(op.dirname(db_eval_file), 'count-%s.png' % suffix)))

