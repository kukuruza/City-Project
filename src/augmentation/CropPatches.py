#!/usr/bin/env python
import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import simplejson as json
import logging
from datetime import datetime
import sqlite3
import numpy as np
from random import choice
from numpy.random import normal, uniform
import scipy.misc
from glob import glob
from math import ceil
import traceback
import shutil
import argparse
from learning.helperSetup import atcity, setupLogging
from learning.helperDb import createDb, makeTimeString
from learning.dbUtilities import expandRoiToRatio, expandRoiFloat, bbox2roi, mask2bbox
from learning.helperImg import SimpleWriter, imread, imsave

OUT_INFO_NAME    = 'out_info.json'



def crop_patches (patch, mask, bbox, expand_perc, keep_ratio, target_width, target_height):
    '''Crop patches in patch_dir directory according to their masks.
    Args:
      patch_dir:     dir with files depth-all.png, depth-car.png
    Returns:
      cropped image
    '''
    MIN_BBOX_SIZE = 10

    assert patch is not None
    assert mask is not None and mask.dtype == bool
    assert patch.shape[0:2] == mask.shape[0:2]

    roi = bbox2roi(bbox)
    ratio = float(target_height) / target_width
    if keep_ratio:
      expandRoiToRatio (roi, 0, ratio)
    expandRoiFloat (roi, (expand_perc, expand_perc))
    roi = [int(x) for x in roi]

    target_shape = (target_height, target_width)
    if roi[2]-roi[0] < MIN_BBOX_SIZE or roi[3] - roi[1] < MIN_BBOX_SIZE:
      logging.error('The crop is too small. Roi: %s' % str(roi))
      raise Exception('The crop is too small.')

    mask = mask.astype(np.uint8)
    crop_patch = patch[roi[0]:roi[2]+1, roi[1]:roi[3]+1, :]
    crop_mask  = mask [roi[0]:roi[2]+1, roi[1]:roi[3]+1]
    crop_patch = scipy.misc.imresize(crop_patch, target_shape, 'bilinear')
    crop_mask  = scipy.misc.imresize(crop_mask,  target_shape, 'nearest')
    crop_mask = crop_mask.astype(bool)
    return crop_patch, crop_mask



def write_visible_mask (patch_dir):
    '''Write the mask of the car visible area
    '''
    logging.debug ('making a mask in %s' % patch_dir)
    mask_path = op.join(patch_dir, 'mask.png')

    depth_all = imread(op.join(patch_dir, 'depth-all.png'))
    depth_car = imread(op.join(patch_dir, 'depth-car.png'))
    assert depth_all is not None
    assert depth_car is not None

    # full main car mask (including occluded parts)
    mask_car = (depth_car < 255*255)

    bbox = mask2bbox(mask_car)
    if bbox is None:
        raise Exception('Mask is empty. Car is outside of the image.')

    # main_car mask of visible regions
    visible_car = depth_car == depth_all
    un_mask_car = np.logical_not(mask_car)
    visible_car[un_mask_car] = False
    imsave(mask_path, visible_car.astype(np.uint8)*255)
    return visible_car, bbox



def get_visible_perc (patch_dir, visible_car):
    '''Some parts of the main car is occluded. 
    Calculate the percentage of the occluded part.
    Args:
      patch_dir:     dir with files depth-all.png, depth-car.png
    Returns:
      visible_perc:  occluded fraction
      bbox:          bounding box is calculated on visible AND occluded parts.
    '''
    #visible_car = imread(op.join(patch_dir, 'mask.png'), 0) > 0
    mask_car    = imread(op.join(patch_dir, 'depth-car.png')) < 255*255
    assert visible_car is not None
    assert mask_car is not None

    # visible percentage
    nnz_car     = np.count_nonzero(mask_car)
    nnz_visible = np.count_nonzero(visible_car)
    visible_perc = float(nnz_visible) / nnz_car
    logging.debug ('visible perc: %0.2f' % visible_perc)
    return visible_perc

    

if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('--in_dir',  default='data/augmentation/patches/test')
  parser.add_argument('--out_dir', default='data/augmentation/patches/test_crops')
  parser.add_argument('--expand_perc',   type=float, default=0.1)
  parser.add_argument('--target_width',  type=int,   default=40)
  parser.add_argument('--target_height', type=int,   default=30)
  parser.add_argument('--keep_ratio', action='store_true',
                      help='do not distort the patch, and increase bbox if needed')
  parser.add_argument('--logging_level', type=int,   default=20,
                      choices={10,20,30,40,50})

  args = parser.parse_args()

  MIN_MASK_NNZ = 100

  setupLogging('log/augmentation/CropPatches.log', args.logging_level, 'w')

  # delete and recreate out_dir dir
  if op.exists(atcity(args.out_dir)):
      shutil.rmtree(atcity(args.out_dir))
  os.makedirs(atcity(args.out_dir))

  # image writer
  image_writer = SimpleWriter(vimagefile=op.join(args.out_dir, 'patch.avi'),
                              vmaskfile=op.join(args.out_dir, 'mask.avi'))

  db_path = op.join(args.out_dir, 'patch.db')
  conn = sqlite3.connect(db_path)
  createDb(conn)
  c = conn.cursor()

  i_patch = 0
  for in_scene_dir in glob(atcity(op.join(args.in_dir, 'scene-??????'))):
    scene_name = op.basename(in_scene_dir)

    try:
      for patch_dir in glob(op.join(in_scene_dir, '??????')):
        mask, bbox = write_visible_mask (patch_dir)
        visible_perc = get_visible_perc (patch_dir, mask)
        if visible_perc == 0: 
          logging.warning('nothing visibible for %s' % patch_dir)
          continue
        patch = imread(op.join(patch_dir, 'render.png'))
        patch, mask = crop_patches(patch, mask, bbox,
                                   args.expand_perc, args.keep_ratio,
                                   args.target_width, args.target_height)
        assert mask.dtype == bool, mask.dtype
        if np.count_nonzero(mask) < MIN_MASK_NNZ:
          raise Exception('nothing visible in the mask')

        # read angles
        out_info = json.load(open( op.join(patch_dir, OUT_INFO_NAME) ))

        # something went wrong, probably the mask is empty
        if patch is None or mask is None: continue

        # write cropped image
        logging.debug(str((patch.shape, patch.dtype, mask.shape, mask.dtype)))
        image_writer.imwrite(patch[...,:3])
        image_writer.maskwrite(mask)
        logging.info ('wrote cropped patch: %d' % i_patch)

        imagefile = op.join(args.out_dir, 'patch', '%06d' % i_patch)
        bbox = mask2bbox(mask)
        name = out_info['vehicle_type']
        yaw = out_info['azimuth']
        pitch = out_info['altitude']
        s = 'cars(imagefile,name,x1,y1,width,height,score,yaw,pitch)'
        c.execute('INSERT INTO %s VALUES (?,?,?,?,?,?,?,?,?);' % s,
            (imagefile, name, bbox[0], bbox[1], bbox[2], bbox[3], visible_perc, yaw, pitch))

        # write to .db
        maskfile = op.join(args.out_dir, 'mask', '%06d' % i_patch)
        w = args.target_width
        h = args.target_height
        timestamp = makeTimeString(datetime.now())
        s = 'images(imagefile,maskfile,src,width,height,time)'
        c.execute ('INSERT INTO %s VALUES (?,?,?,?,?,?);' % s,
            (imagefile, maskfile, '' , w, h, timestamp))

        i_patch += 1
#      if i_patch > 200:
#        conn.commit()
#        conn.close()
#        break
    except:
      logging.error('postprocessing failed for patch %s: %s' %
                    (patch_dir, traceback.format_exc()))

  conn.commit()
  conn.close()
