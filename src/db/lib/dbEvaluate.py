import os, os.path as op
import sys
import logging
import sqlite3
import numpy as np
from progressbar import ProgressBar
from helperSetup import dbInit
from helperDb    import carField
from helperImg   import ReaderVideo



def add_parsers(subparsers):
  evaluateDetectionParser(subparsers)
  evaluateSegmentationParser(subparsers)


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


def evaluateDetectionParser(subparsers):
  parser = subparsers.add_parser('evaluateDetection',
    description='Evaluate detections in the open db w.r.t. a ground truth db.')
  parser.set_defaults(func=evaluateDetection)
  parser.add_argument('--gt_db_file', required=True)
  parser.add_argument('--overlap_thresh', type=float, default=0.5)
  parser.add_argument('--gt_car_constraint', default='1')
  parser.add_argument('--image_constraint', default='1')


def evaluateDetection (c, args):
  logging.info ('==== evaluateDetection ====')

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



def fast_hist(a, b, n):
  k = (a >= 0) & (a < n)
  return np.bincount(n * a[k].astype(int) + b[k], minlength=n ** 2).reshape(n, n)

def per_class_iu(hist):
  return np.diag(hist) / (hist.sum(1) + hist.sum(0) - np.diag(hist))

def calc_fw_iu(hist):
  pred_per_class = hist.sum(0)
  gt_per_class = hist.sum(1)
  return np.nansum(
      (gt_per_class * np.diag(hist)) / (pred_per_class + gt_per_class - np.diag(hist))) / gt_per_class.sum()

def calc_pixel_accuracy(hist):
  gt_per_class = hist.sum(1)
  return np.diag(hist).sum() / gt_per_class.sum()

def calc_mean_accuracy(hist):
  gt_per_class = hist.sum(1)
  acc_per_class = np.diag(hist) / gt_per_class
  return np.nanmean(acc_per_class)

def save_colorful_images(prediction, filename, palette, postfix='_color.png'):
  im = Image.fromarray(palette[prediction.squeeze()])
  im.save(filename[:-4] + postfix)

def label_mapping(input, mapping):
  output = np.copy(input)
  for ind in range(len(mapping)):
    output[input == mapping[ind][0]] = mapping[ind][1]
  return np.array(output, dtype=np.int64)

def plot_confusion_matrix(cm, classes,
    normalize=False, title='Confusion matrix', cmap=None):
  """
  This function prints and plots the confusion matrix.
  Normalization can be applied by setting `normalize=True`.
  """
  import matplotlib
  matplotlib.use('Agg')
  from matplotlib import pyplot as plt

  if cmap is None:
    cmap = plt.cm.Blues

  if normalize:
    cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    logging.info("Normalized confusion matrix.")
  else:
    logging.info('Confusion matrix will be computed without normalization.')

  plt.imshow(cm, interpolation='nearest', cmap=cmap)
  plt.colorbar()
  tick_marks = np.arange(len(classes))
  plt.xticks(tick_marks, classes, rotation=90)
  plt.yticks(tick_marks, classes)

  fmt = '.2f' if normalize else 'd'
  thresh = cm.max() / 2.
  plt.tight_layout()
  plt.ylabel('Ground truth')
  plt.xlabel('Predicted label')

def evaluateSegmentationParser(subparsers):
  parser = subparsers.add_parser('evaluateSegmentation',
    description='Evaluate mask segmentation w.r.t. a ground truth db.')
  parser.set_defaults(func=evaluateSegmentation)
  parser.add_argument('--gt_db_file', required=True)
  parser.add_argument('--image_constraint', default='1')
  parser.add_argument('--out_dir',
      help='If specified, result files with be written there.')
  parser.add_argument('--out_prefix', default='',
      help='Add to filenames')

def evaluateSegmentation(c, args):
  logging.info ('==== evaluateSegmentation ====')
  import pandas as pd

  (conn_gt, c_gt) = dbInit(args.gt_db_file)

  # WARNING:
  # The assumption is that the imagefiles may be different
  #   but images are the still the same.

  s = ('SELECT imagefile, maskfile FROM images '
       'WHERE %s ORDER BY imagefile ASC' % args.image_constraint)
  logging.debug(s)

  c.execute(s)
  entries_pred = c.fetchall()
  logging.info ('Total %d images in predicted.' % len(entries_pred))

  c_gt.execute(s)
  entries_gt = c_gt.fetchall()
  logging.info ('Total %d images in gt.' % len(entries_gt))

  assert len(entries_pred) == len(entries_gt)

  reader = ReaderVideo(relpath=args.relpath)
  reader_gt = ReaderVideo()  # Has no relpath.

  hist = np.zeros((2, 2))

  for entry_pred, entry_gt in ProgressBar()(zip(entries_pred, entries_gt)):
    imagefile_pred, maskfile_pred = entry_pred
    imagefile_gt, maskfile_gt = entry_gt

    mask_pred = reader.maskread(maskfile_pred).astype(int)
    mask_gt = reader_gt.maskread(maskfile_gt).astype(int)

    hist += fast_hist(mask_gt.flatten(), mask_pred.flatten(), 2)

  # Get label distribution
  pred_per_class = hist.sum(0)
  gt_per_class = hist.sum(1)

  used_class_id_list = np.where(gt_per_class != 0)[0]
  hist = hist[used_class_id_list][:, used_class_id_list]  # Extract only GT existing (more than 1) classes

  class_list = np.array(['background', 'car'])[used_class_id_list]

  iou_list = per_class_iu(hist)
  fwIoU = calc_fw_iu(hist)
  pixAcc = calc_pixel_accuracy(hist)
  mAcc = calc_mean_accuracy(hist)

  result_df = pd.DataFrame({
      'class': ['background', 'car'],
      'IoU': iou_list,
      "pred_distribution": pred_per_class[used_class_id_list],
      "gt_distribution": gt_per_class[used_class_id_list],
  })
  result_df["IoU"] = result_df["IoU"] * 100  # change to percent ratio

  result_df.set_index("class", inplace=True)
  print("---- info per class -----")
  print(result_df)

  result_ser = pd.Series({
      "pixAcc": pixAcc,
      "mAcc": mAcc,
      "fwIoU": fwIoU,
      "mIoU": iou_list.mean()
  })
  result_ser = result_ser[["pixAcc", "mAcc", "fwIoU", "mIoU"]]
  result_ser *= 100  # change to percent ratio

  print("---- total result -----")
  print(result_ser)

  if args.out_dir is not None:
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt

    if not op.exists(args.out_dir):
      os.makedirs(args.out_dir)

    # Save confusion matrix
    fig = plt.figure()
    normalized_hist = hist.astype("float") / hist.sum(axis=1)[:, np.newaxis]

    plot_confusion_matrix(normalized_hist, classes=class_list, title='Confusion matrix')
    outfigfn = os.path.join(args.out_dir, "%sconf_mat.pdf" % args.out_prefix)
    fig.savefig(outfigfn, transparent=True, bbox_inches='tight', pad_inches=0, dpi=300)
    print("Confusion matrix was saved to %s" % outfigfn)

    outdffn = os.path.join(args.out_dir, "%seval_result_df.csv" % args.out_prefix)
    result_df.to_csv(outdffn)
    print('Info per class was saved at %s !' % outdffn)
    outserfn = os.path.join(args.out_dir, "%seval_result_ser.csv" % args.out_prefix)
    result_ser.to_csv(outserfn)
    print('Total result is saved at %s !' % outserfn)

