import os, sys, os.path as op
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
from learning.helperSetup import setupLogging, dbInit, atcity
from learning.dbEvaluate  import evalClass, evalCounting
from learning.dbModify import filterCustom
import matplotlib.pyplot as plt



setupLogging ('log/detector/EvaluateDetections.log', logging.INFO, 'a')

db_eval_file = 'faster-rcnn/572-Feb23-09h-Jan27/train-Jan29/real_detected_with_30K.db'
db_true_file = 'faster-rcnn/572-Feb23-09h-Jan27/labelled-filt-test-e02-w25.db'

# sinthetic_range_contraint = {
#   'image_constraint': 
#     'imagefile >= "camdata/cam572/Feb23-09h/src/000100" AND '
#     'imagefile <  "camdata/cam572/Feb23-09h/src/004000"',
#   'car_constraint': 'y1 + height > 300'}

(conn_true, cursor_true) = dbInit(db_true_file, backup=False)
(conn_eval, cursor_eval) = dbInit(db_eval_file, backup=False)
# filterCustom(cursor_true, sinthetic_range_contraint)
# filterCustom(cursor_eval, sinthetic_range_contraint)
# trained model has some strange failures near the bottom right corner
#filterCustom(cursor_eval, {'car_constraint': 'y1 < 450 OR y1 + height < 470'})

rec, prec, ap = evalClass (cursor_eval, cursor_true, classname=None)
det_counts, gt_counts = evalCounting (cursor_eval, cursor_true, classname=None)

conn_eval.close()
conn_true.close()

# print 'ap: %0.3f' % ap
# ax = plt.subplot(111)
# plt.plot(rec, prec)
# plt.xlabel('recall')
# plt.ylabel('precision')
# #plt.title('labelled frames')
# ax.set_xlim([0,1])
# ax.set_ylim([0,1])
# plt.grid(True)
# plt.savefig(atcity(op.join(op.dirname(db_eval_file), 'ROC.png')))

t = range(len(det_counts))
ax = plt.subplot(111)
plt.plot(t, det_counts, 'r')
plt.plot(t, gt_counts, 'b')
plt.xlabel('frame id')
plt.ylabel('count')
#plt.title('labelled frames')
# ax.set_xlim([0,1])
# ax.set_ylim([0,1])
plt.grid(True)
plt.savefig(atcity(op.join(op.dirname(db_eval_file), 'count.png')))
