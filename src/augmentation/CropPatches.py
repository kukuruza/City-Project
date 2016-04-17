#!/usr/bin/env python
import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import json
import logging
import numpy as np
from random import choice
from numpy.random import normal, uniform
import cv2
from glob import glob
from math import ceil
import traceback
import shutil
import argparse
from learning.helperSetup import atcity, setupLogging
from learning.dbUtilities import expandRoiToRatio, expandRoiFloat, bbox2roi, mask2bbox

OUT_INFO_NAME    = 'out_info.json'
EXT = 'jpg'  # format of output patches



def crop_patches (patch_dir, expand_perc, keep_ratio, target_width, target_height):
    '''Crop patches in patch_dir directory according to their masks.
    Args:
      patch_dir:     dir with files depth-all.png, depth-car.png
    Returns:
      cropped image
    '''
    try:
        patch = cv2.imread(op.join(patch_dir, 'render.png'))
        mask  = cv2.imread(op.join(patch_dir, 'mask.png'), 0)
        assert patch is not None
        assert mask is not None and mask.dtype == np.uint8
        assert patch.shape[0:2] == mask.shape[0:2]

        bbox = mask2bbox(mask)
        if bbox is None:
            raise Exception('Mask is empty. Car is outside of the image.')
        roi = bbox2roi(bbox)
        ratio = float(target_height) / target_width
        imshape = (patch.shape[0], patch.shape[1])
        if keep_ratio:
          expandRoiToRatio (roi, imshape, 0, ratio)
        expandRoiFloat   (roi, imshape, (expand_perc, expand_perc))

        target_shape = (target_width, target_height)

        crop_patch = patch[roi[0]:roi[2]+1, roi[1]:roi[3]+1, :]
        crop_mask  = mask [roi[0]:roi[2]+1, roi[1]:roi[3]+1]
        crop_patch = cv2.resize(crop_patch, target_shape) # cv2.INTER_LINEAR)
        crop_mask  = cv2.resize(crop_mask,  target_shape, interpolation=cv2.INTER_NEAREST)
        return (crop_patch, crop_mask)
    except:
        logging.error('crop for %s failed: %s' % (patch_dir, traceback.format_exc()))
        return (None, None)



def write_visible_mask (patch_dir):
    '''Write the mask of the car visible area
    '''
    logging.debug ('making a mask in %s' % patch_dir)
    mask_path = op.join(patch_dir, 'mask.png')

    depth_all = cv2.imread(op.join(patch_dir, 'depth-all.png'), -1)
    depth_car = cv2.imread(op.join(patch_dir, 'depth-car.png'), -1)
    assert depth_all is not None
    assert depth_car is not None

    # full main car mask (including occluded parts)
    mask_car = (depth_car < 255*255)
    # main_car mask of visible regions
    visible_car = depth_car == depth_all
    un_mask_car = np.logical_not(mask_car)
    visible_car[un_mask_car] = False
    cv2.imwrite(mask_path, visible_car.astype(np.uint8)*255)



def get_visible_perc (patch_dir):
    '''Some parts of the main car is occluded. 
    Calculate the percentage of the occluded part.
    Args:
      patch_dir:     dir with files depth-all.png, depth-car.png
    Returns:
      visible_perc:  occluded fraction
    '''
    visible_car = cv2.imread(op.join(patch_dir, 'mask.png'), 0) > 0
    mask_car    = cv2.imread(op.join(patch_dir, 'depth-car.png'), -1) < 255*255
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
    parser.add_argument('--in_dir',  default='augmentation/patches/test')
    parser.add_argument('--out_dir', default='augmentation/patches/test_crops')
    parser.add_argument('--logging_level',   type=int,   default=20)
    parser.add_argument('--expand_perc',     type=float, default=0.1)
    parser.add_argument('--target_width',    type=int,   default=40)
    parser.add_argument('--target_height',   type=int,   default=30)
    parser.add_argument('--keep_ratio', action='store_true',
                        help='do not distort the patch, and increase bbox if needed')

    args = parser.parse_args()

    setupLogging('log/augmentation/CropPatches.log', args.logging_level, 'w')


    # delete and recreate out_dir dir
    if op.exists(atcity(args.out_dir)):
        shutil.rmtree(atcity(args.out_dir))
    os.makedirs(atcity(args.out_dir))

    ids_f = open(atcity(op.join(args.out_dir, 'ids.txt')), 'w')
    vis_f = open(atcity(op.join(args.out_dir, 'visibility.txt')), 'w')
    roi_f = open(atcity(op.join(args.out_dir, 'roi.txt')), 'w')
    typ_f = open(atcity(op.join(args.out_dir, 'types.txt')), 'w')
    ang_f = open(atcity(op.join(args.out_dir, 'angles.txt')), 'w')

    for in_scene_dir in glob(atcity(op.join(args.in_dir, 'scene-??????'))):
        scene_name = op.basename(in_scene_dir)
        out_scene_dir = atcity(op.join(args.out_dir, scene_name))
        os.makedirs(out_scene_dir)

        for patch_dir in glob(op.join(in_scene_dir, '??????')):
          try:
            write_visible_mask (patch_dir)
            visible_perc = get_visible_perc (patch_dir)
            if visible_perc == 0: 
                logging.warning('nothing visibible for %s' % patch_dir)
                continue
            patch, mask = crop_patches(patch_dir, args.expand_perc, args.keep_ratio,
                                       args.target_width, args.target_height)

            # something went wrong, probably the mask is empty
            if patch is None or mask is None: continue

            # write cropped image and visible_perc and remove the source dir
            patch_name = '%sp.%s' % (op.basename(patch_dir), EXT)
            mask_name  = '%sm.png' % op.basename(patch_dir)
            patch_path = op.join(out_scene_dir, patch_name)
            mask_path  = op.join(out_scene_dir, mask_name)
            retval_img  = cv2.imwrite(patch_path, patch)
            retval_mask = cv2.imwrite(mask_path, mask)
            if not retval_img or not retval_mask:
              logging.error ('failed with cropped patch: %s/%s' % (scene_name, patch_name))
            else:
              logging.info ('wrote cropped patch: %s/%s' % (scene_name, patch_name))

            # read angles
            out_info = json.load(open( op.join(patch_dir, OUT_INFO_NAME) ))

            # write ids, bboxes, visibility, and angles
            patch_id = op.join(scene_name, op.splitext(patch_name)[0])
            bbox = mask2bbox (mask)
            assert bbox is not None
            roi_str = ' '.join([str(x) for x in bbox2roi(bbox)])
            roi_f.write('%s %s\n' % (patch_id, roi_str)) # [y1 x1 y2 x2]
            vis_f.write('%s %f\n' % (patch_id, visible_perc))
            ids_f.write('%s\n'    %  patch_id)
            typ_f.write('%s %s\n' % (patch_id, out_info['vehicle_type']))
            ang_f.write('%s %.2f %.2f\n' % 
                        (patch_id, out_info['azimuth'], out_info['altitude']))
          except:
            logging.error('postprocessing failed for patch %s: %s' %
                          (patch_dir, traceback.format_exc()))

    ids_f.close()
    vis_f.close()
    roi_f.close()
    typ_f.close()
    ang_f.close()
