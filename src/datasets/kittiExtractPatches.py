#!/usr/bin/env python
import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
from glob import glob
import shutil
import argparse
import logging
import cv2
import numpy as np
from math import pi, floor
from learning.helperSetup import atcity, setupLogging, setParamUnlessThere
from learning.dbUtilities import expandRoiToRatio, expandRoiFloat


def _convert_type(kitti_type):
  if   kitti_type == 'Car': return 'passenger'
  elif kitti_type == 'Van': return 'van'
  elif kitti_type == 'Truck': return 'truck'
  elif kitti_type == 'Pedestrian': return 'pedestrian'
  elif kitti_type == 'Cyclist': return 'bike'
  else: return 'object'


def extract_patches (in_base_dir, out_base_dir, params={}):

  setParamUnlessThere (params, 'debug_show',  False)
  setParamUnlessThere (params, 'expand_perc', 0)
  setParamUnlessThere (params, 'target_width',  40)
  setParamUnlessThere (params, 'target_height', 30)
  setParamUnlessThere (params, 'keep_ratio',  False)

  # recreate out_base_dir
  if op.exists(atcity(out_base_dir)):
    shutil.rmtree(atcity(out_base_dir))
  os.makedirs(atcity(out_base_dir))

  # start files: ids, types, angles, rois
  ids_f = open(atcity(op.join(out_base_dir, 'ids.txt')), 'w')
  vis_f = open(atcity(op.join(out_base_dir, 'visibility.txt')), 'w')
#  roi_f = open(atcity(op.join(out_base_dir, 'roi.txt')), 'w')
  typ_f = open(atcity(op.join(out_base_dir, 'types.txt')), 'w')
  ang_f = open(atcity(op.join(out_base_dir, 'angles.txt')), 'w')

  # list images in in_base_dir/image_2
  imagepaths = glob(atcity(op.join(in_base_dir, 'image_2', '*.png')))

  patch_id = 0
  for imagepath in imagepaths:

    # read the annotations.
    labelpath = op.join(op.dirname(op.dirname(imagepath)), 'label_2', 
                        '%s.txt' % op.splitext(op.basename(imagepath))[0])
    with open(labelpath) as f:
      annotation_lines = f.read().splitlines()

    if not annotation_lines:
      continue

    img = cv2.imread(imagepath)
    assert img is not None

    for i,annotation_line in enumerate(annotation_lines):
      dir_id = int(floor(float(patch_id) / params['patches_per_dir']))

      # get roi, vehicle_type, angle, visibility
      (vehicle_type, truncated, occluded, alpha, left, top, right, bottom) = \
        tuple(annotation_line.split()[:8])
      vehicle_type = _convert_type(vehicle_type)
      roi = [top, left, bottom, right]
      roi = [int(float(x)) for x in roi]
      roi = [roi[0], roi[1], roi[2]+1, roi[3]+1]
      azimuth = (float(alpha) * 180 / pi) % 360
      azimuth = (270 - azimuth) % 360   # to keep consistent
      if bool(float(truncated)):
        visibility = 0.3
      elif int(occluded) == 0:
        visibility = 1.0
      elif int(occluded) == 1:
        visibility = 0.7
      elif int(occluded) == 2:
        visibility = 0.3
      elif int(occluded) == 3:
        logging.warning ('skip object #%d in %s with unknown visibility' %
                         (i, labelpath))
        continue
      else:
        raise Exception('wrong case')

      logging.info ('vehicle_type: %s, roi: %s, azimuth: %s, visibility: %f' %
                    (vehicle_type, roi, azimuth, visibility))

      if vehicle_type not in ['passenger', 'van', 'truck']:
        logging.debug ('skip object %s' % vehicle_type)
        continue

      # expand roi
      expand_perc = params['expand_perc']
      imshape = tuple(img.shape[:2])
      if params['keep_ratio']:
        roi = expandRoiToRatio (roi, imshape, 0, params['ratio'])
      roi = expandRoiFloat   (roi, imshape, (expand_perc, expand_perc))

      patch_dir = '%06d' % dir_id
      if not op.exists(atcity(op.join(out_base_dir, patch_dir))):
        os.makedirs(atcity(op.join(out_base_dir, patch_dir)))

      # extract its patch
      patch_str = op.join(patch_dir, '%08d' % patch_id)
      patch = img[roi[0]:roi[2], roi[1]:roi[3], :]

      # resize its patch
      target_shape = (params['target_width'], params['target_height'])
      patch = cv2.resize(patch, target_shape) # cv2.INTER_LINEAR)

      cv2.imwrite(atcity(op.join(out_base_dir, '%s.jpg' % patch_str)), patch)

      if params['debug_show']:
        cv2.imshow('img', img)
        key = cv2.waitKey(-1)
        if key == 27:
          debug_show = False

      # write id, vehicle_type, angle
      ids_f.write('%s\n' % patch_str)
      vis_f.write('%s %.2f\n' % (patch_str, visibility))
#      roi_f.write('%s %d %d %d %d\n' % patch_str)
      typ_f.write('%s %s\n' % (patch_str, vehicle_type))
      ang_f.write('%s %.2f 0.0\n' % (patch_str, azimuth))

      patch_id += 1


  ids_f.close()
  vis_f.close()
#  roi_f.close()
  typ_f.close()
  ang_f.close()



if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('--in_base_dir')
  parser.add_argument('--out_base_dir')
  parser.add_argument('--patches_per_dir', type=int, default=10,
                      help='number of patches to put in each subdir')
  parser.add_argument('--expand_perc', type=float, default=0.0,
                      help='expand patches by %% on each side')
  parser.add_argument('--target_width',    type=int,   default=40)
  parser.add_argument('--target_height',   type=int,   default=30)
  parser.add_argument('--keep_ratio', action='store_true',
                      help='do not distort the patch, and increase bbox if needed')
  parser.add_argument('--debug_show', action='store_true')

  args = parser.parse_args()

  params = {'expand_perc': args.expand_perc,
            'target_width': args.target_width,
            'target_height': args.target_height,
            'keep_ratio': args.keep_ratio,
            'patches_per_dir': args.patches_per_dir,
            'debug_show': args.debug_show}

  extract_patches (args.in_base_dir, args.out_base_dir, params)
