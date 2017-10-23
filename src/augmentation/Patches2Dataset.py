#!/usr/bin/env python
import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import simplejson as json
import logging
import numpy as np
from glob import glob
import argparse
from db.lib.helperSetup import atcity
from db.lib.dbUtilities import bbox2roi, mask2bbox
from db.lib.helperImg import imread, imsave
from db.lib.dbExport import DatasetWriter

OUT_INFO_NAME    = 'out_info.json'


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
  parser.add_argument('--in_dir',  default='data/patches/test')
  parser.add_argument('--out_db_file', default='data/patches/test/scenes.db')
  args = parser.parse_args()

  MIN_MASK_NNZ = 100

  dataset_writer = DatasetWriter(args.out_db_file, overwrite=True)

  for in_scene_dir in glob(atcity(op.join(args.in_dir, 'scene-??????'))):
    scene_name = op.basename(in_scene_dir)

    for patch_dir in glob(op.join(in_scene_dir, '??????')):
      mask, bbox = write_visible_mask (patch_dir)
      visible_perc = get_visible_perc (patch_dir, mask)
      if visible_perc == 0: 
        logging.warning('nothing visibible for %s' % patch_dir)
        continue
      patch = imread(op.join(patch_dir, 'render.png'))[:,:,:3]
      imagefile = dataset_writer.add_image(patch, mask=mask)

      out_info = json.load(open( op.join(patch_dir, OUT_INFO_NAME) ))
      bbox = mask2bbox(mask)
      name = out_info['vehicle_type']
      yaw = out_info['azimuth']
      pitch = out_info['altitude']
      car = (imagefile, name, bbox[0], bbox[1], bbox[2], bbox[3], visible_perc, yaw, pitch)
      dataset_writer.add_car(car)
  dataset_writer.close()
