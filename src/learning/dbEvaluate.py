import os, os.path as op
import sys
import logging
import sqlite3
import numpy as np


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


def evalClass (c_gt, c_det, classname=None, ovthresh=0.5):
  """ PASCAL VOC evaluation of a specific class or all detections.
  Args:
    c_gt:      cursor to the sqlite3 db with ground truth
    c_out:     cursor to the sqlite3 db with detections
    classname: category name (duh). If None, then any category
    ovthresh:  overlap threshold (default = 0.5)
  """

  if classname is None:
    c_det.execute('SELECT imagefile,x1,y1,width,height,score FROM cars '
                  'ORDER BY score DESC')
  else:
    c_det.execute('SELECT imagefile,x1,y1,width,height,score FROM cars '
                  'ORDER BY score DESC '
                  'WHERE name=?', (classname,))
  cars_det = c_det.fetchall()
  print 'Total %d cars_det of class %s' % (len(cars_det), classname)

  # go down dets and mark TPs and FPs
  tp = np.zeros(len(cars_det), dtype=float)
  fp = np.zeros(len(cars_det), dtype=float)

  # 'already_detected' used to penalize multiple detections of same GT box
  already_detected = set()

  # go through each detection
  for idet,(imagefile,x1,y1,width,height,score) in enumerate(cars_det):

    bbox_det = np.array([x1,y1,width,height], dtype=float)

    # get all GT boxes from the same imagefile [of the same class]
    if classname is None:
      c_gt.execute('SELECT id,x1,y1,width,height FROM cars '
                   'WHERE imagefile=?', (imagefile,))
    else:
      c_gt.execute('SELECT id,x1,y1,width,height FROM cars '
                   'WHERE imagefile=? AND name=?', (imagefile,classname))
    entries = c_gt.fetchall()
    carids_gt = [entry[0] for entry in entries]
    bboxes_gt = np.array([list(entry[1:]) for entry in entries], dtype=float)

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

    # if 1) large enough overlap and 2) this GT box was not detected before
    if max_overlap > ovthresh and not carid_gt in already_detected:
      tp[idet] = 1.
      already_detected.add(carid_gt)
    else:
      fp[idet] = 1.

  # find the number of GT
  if classname is None:
    c_gt.execute('SELECT COUNT(*) FROM cars')
  else:
    c_gt.execute('SELECT COUNT(*) FROM cars WHERE name=?', (classname,))
  n_gt = c_gt.fetchone()[0]

  # compute precision-recall
  fp = np.cumsum(fp)
  tp = np.cumsum(tp)
  rec = tp / float(n_gt)
  # avoid divide by zero in case the first detection matches a difficult
  # ground truth
  prec = tp / np.maximum(tp + fp, np.finfo(np.float64).eps)
  ap = _voc_ap(rec, prec)

  return rec, prec, ap


def evalCounting (c_gt, c_det, classname=None):
  """ Counting on every time step.
  TODO: right now just all scores, FN < FT anyway
  Args:
    c_gt:      cursor to the sqlite3 db with ground truth
    c_out:     cursor to the sqlite3 db with detections
    classname: category name (duh). If None, then any category
  """

  c_det.execute('SELECT imagefile FROM images')
  imagefiles = c_det.fetchall()
  numimages = len(imagefiles)
  logging.info ('have %d imagefiles' % numimages)

  det_counts = np.zeros(shape=(numimages,), dtype=int)
  gt_counts  = np.zeros(shape=(numimages,), dtype=int)

  for i,(imagefile,) in enumerate(imagefiles): # no GROUP BY because of empty images

    if classname is None:
      c_det.execute('SELECT COUNT(*) FROM cars WHERE imagefile=?', (imagefile,))
    else:
      c_det.execute('SELECT COUNT(*) FROM cars WHERE imagefile=?'
                    ' AND name=?', (imagefile, classname))
    det_counts[i] = int(c_det.fetchone()[0])

    if classname is None:
      c_gt.execute('SELECT COUNT(*) FROM cars WHERE imagefile=?', (imagefile,))
    else:
      c_gt.execute('SELECT COUNT(*) FROM cars WHERE imagefile=?'
                    ' AND name=?', (imagefile, classname))
    gt_counts[i] = int(c_gt.fetchone()[0])

  det_counts = np.cumsum(det_counts)
  gt_counts = np.cumsum(gt_counts)

  return det_counts, gt_counts

