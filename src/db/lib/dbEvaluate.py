import os, os.path as op
import sys
import logging
import sqlite3
import numpy as np
from progressbar import ProgressBar
from helperSetup import dbInit
from helperDb    import carField



def add_parsers(subparsers):
  evaluateIoUParser(subparsers)


def _voc_ap(rec, prec):
  """ Compute VOC AP given precision and recall.
  """

  # first append sentinel values at the end
  mrec = np.concatenate(([0.], rec, [1.]))
  mpre = np.concatenate(([0.], prec, [0.]))

  # compute the precision envelope
  for i in range(mpre.size - 1, 0, -1):
      mpre[i - 1] = np.maximum(mpre[i - 1], mpre[i])

  # to calculate area under PR curve, look for points
  # where X axis (recall) changes value
  i = np.where(mrec[1:] != mrec[:-1])[0]

  # and sum (\Delta recall) * prec
  ap = np.sum((mrec[i + 1] - mrec[i]) * mpre[i + 1])
  return ap


def evaluateIoUParser(subparsers):
  parser = subparsers.add_parser('evaluateIoU',
    description='Evaluate detections in the open db w.r.t. a ground truth db.')
  parser.set_defaults(func=evaluateIoU)
  parser.add_argument('--gt_db_file', required=True)
  parser.add_argument('--overlap_thresh', type=float, default=0.5)
  parser.add_argument('--gt_car_constraint', default='1')
  parser.add_argument('--image_constraint', default='1')


def evaluateIoU (c, args):
  logging.info ('==== evaluateIoU ====')

  (conn_gt, c_gt) = dbInit(args.gt_db_file)

  c.execute('SELECT imagefile,x1,y1,width,height,score FROM cars '
            'WHERE %s ORDER BY score DESC' % args.image_constraint)
  cars_det = c.fetchall()
  logging.info ('Total %d cars_det' % len(cars_det))

  # go down dets and mark TPs and FPs
  tp = np.zeros(len(cars_det), dtype=float)
  fp = np.zeros(len(cars_det), dtype=float)
  ignored = np.zeros(len(cars_det), dtype=bool)  # detected of no interest

  # 'already_detected' used to penalize multiple detections of same GT box
  already_detected = set()

  # go through each detection
  for idet,(imagefile,x1,y1,width,height,score) in ProgressBar()(enumerate(cars_det)):

    bbox_det = np.array([x1,y1,width,height], dtype=float)

    # get all GT boxes from the same imagefile [of the same class]
    c_gt.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
    entries = c_gt.fetchall()
    carids_gt = [carField(entry, 'id') for entry in entries]
    bboxes_gt = np.array([carField(entry, 'bbox') for entry in entries], dtype=float)

    # separately manage no GT boxes
    if bboxes_gt.size == 0:
      fp[idet] = 1.
      continue

    # intersection
    ixmin = np.maximum(bboxes_gt[:,0], bbox_det[0])
    iymin = np.maximum(bboxes_gt[:,1], bbox_det[1])
    ixmax = np.minimum(bboxes_gt[:,0]+bboxes_gt[:,2], bbox_det[0]+bbox_det[2])
    iymax = np.minimum(bboxes_gt[:,1]+bboxes_gt[:,3], bbox_det[1]+bbox_det[3])
    iw = np.maximum(ixmax - ixmin, 0.)
    ih = np.maximum(iymax - iymin, 0.)
    inters = iw * ih

    # union
    uni = bbox_det[2] * bbox_det[3] + bboxes_gt[:,2] * bboxes_gt[:,3] - inters

    # overlaps
    overlaps = inters / uni
    max_overlap = np.max(overlaps)
    carid_gt = carids_gt[np.argmax(overlaps)]

    # find which cars count towards TP and FN
    c_gt.execute('SELECT * FROM cars '
                 'WHERE imagefile=? AND %s' % args.gt_car_constraint, (imagefile,))
    entries = c_gt.fetchall()
    carids_gt_of_interest = [carField(entry, 'id') for entry in entries]

    # if 1) large enough overlap and 2) this GT box was not detected before
    if max_overlap > args.overlap_thresh and not carid_gt in already_detected:
      if carid_gt in carids_gt_of_interest:
        tp[idet] = 1.
      else:
        ignored[idet] = True
      already_detected.add(carid_gt)
    else:
      fp[idet] = 1.

  # find the number of GT of interest
  c_gt.execute('SELECT COUNT(*) FROM cars WHERE (%s) AND (%s)' % 
               (args.gt_car_constraint, args.image_constraint))
  n_gt = c_gt.fetchone()[0]
  assert n_gt > 0, args.gt_car_constraint
  logging.info ('Total %d cars of interest' % n_gt)

  # remove dets, neither TP or FP
  tp = tp[np.bitwise_not(ignored)]
  fp = fp[np.bitwise_not(ignored)]

  logging.info('ignored: %d, tp: %d, fp: %d, gt: %d' %
               (np.count_nonzero(ignored),
                np.count_nonzero(tp),
                np.count_nonzero(fp),
                n_gt))
  assert np.count_nonzero(tp) + np.count_nonzero(fp) + np.count_nonzero(ignored) == len(cars_det)

  # compute precision-recall
  fp = np.cumsum(fp)
  tp = np.cumsum(tp)
  rec = tp / float(n_gt)
  # avoid divide by zero in case the first detection matches a difficult
  # ground truth
  prec = tp / np.maximum(tp + fp, np.finfo(np.float64).eps)
  ap = _voc_ap(rec, prec)

  conn_gt.close()

  print 'average precision', ap
