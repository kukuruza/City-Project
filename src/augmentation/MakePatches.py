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
import subprocess
import multiprocessing
import traceback
import shutil
import argparse
from learning.helperSetup import atcity, setupLogging
from learning.dbUtilities import expandRoiToRatio, expandRoiFloat, bbox2roi, mask2bbox
from augmentation.Cad import Cad

RESULT_DIR       = atcity('augmentation/patches')
WORK_PATCHES_DIR = atcity('augmentation/blender/current-patch')
PATCHES_HOME_DIR = atcity('augmentation/patches/')
JOB_INFO_NAME    = 'job_info.json'
EXT = 'jpg'  # format of output patches

# placing other cars
PROB_SAME_LANE    = 0.3
SIGMA_AZIMUTH     = 5
SIGMA_SAME        = 0.3
SIGMA_SIDE        = 0.1
MEAN_SAME         = 1.5
MEAN_SIDE         = 1.5

class Diapason:

    def _parse_range_str_ (self, range_str, length):
        '''Parses python range STRING into python range
        '''
        assert isinstance(range_str, basestring)
        # remove [ ] around the range
        if len(range_str) >= 2 and range_str[0] == '[' and range_str[-1] == ']':
            range_str = range_str[1:-1]
        # split into three elements start,end,step. Assign step=1 if missing
        arr = range_str.split(':')
        assert len(arr) == 2 or len(arr) == 3, 'need 1 or 2 commas "," in range string'
        if len(arr) == 2: arr.append('1')
        if arr[0] == '': arr[0] = '0'
        if arr[1] == '': arr[1] = str(length)
        if arr[2] == '': arr[2] = '1'
        start = int(arr[0])
        end   = int(arr[1])
        step  = int(arr[2])
        range_py = range(start, end, step)
        logging.info ('Diapason parsed range_str %s into range of length %d' % (range_str, len(range_py)))
        logging.debug ('Diapason range %s' % range_py)
        return range_py

    def __init__ (self, length, range_str):
        self._range = self._parse_range_str_ (range_str, length)

    def filter_list (self, in_list):
        return [el for i,el in enumerate(in_list) if i in self._range]



def pick_spot_for_a_vehicle (dims0, model):
    '''Given car dimensions, randomly pick a spot around the main car

    Args:
      dims0:     dict with fields 'x' and 'y' for the main model
      model:     a dict with field 'dims'
    Returns:
      vehicle:   same as model, but with x,y,azimuth fields
    '''
    # in the same lane or on the lanes on the sides
    is_in_same_lane = (uniform() < PROB_SAME_LANE)

    # define probabilities for other vehicles
    if is_in_same_lane:
        x = normal(MEAN_SAME, SIGMA_SAME) * choice([-1,1])
        y = normal(0, SIGMA_SAME)
    else: 
        x = normal(0, 1.5)
        y = normal(MEAN_SIDE, SIGMA_SIDE) * choice([-1,1])

    # normalize to our car size
    x *= (dims0['x'] + model['dims']['x']) / 2
    y *= (dims0['y'] + model['dims']['y']) / 2
    azimuth = normal(0, SIGMA_AZIMUTH) + 90
    vehicle = model
    vehicle['x'] = x
    vehicle['y'] = y
    vehicle['azimuth'] = azimuth
    return vehicle



def place_occluding_vehicles (vehicle0, other_models):
    '''Distributes existing models across the scene.
    Vehicle[0] is the main photo-session character. It is in the center.

    Args:
      vehicles0:       main model dict with x,y,azimuth
      other_models:    dicts without x,y,azimuth
    Returns:
      other_vehicles:  same as other_models, but with x,y,azimuth fields
    '''
    vehicles = []
    for i,model in enumerate(other_models):
        logging.debug ('place_occluding_vehicles: try %d on model_id %s' 
                       % (i, model['model_id']))

        # pick its location and azimuth
        assert 'dims' in vehicle0, '%s' % json.dumps(vehicle0, indent=4)
        vehicle = pick_spot_for_a_vehicle(vehicle0['dims'], model)

        # find if it intersects with anything (cars are almost parallel)
        x1     = vehicle['x']
        y1     = vehicle['y']
        dim_x1 = vehicle['dims']['x']
        dim_y1 = vehicle['dims']['y']
        does_intersect = False
        # compare to all previous vehicles (O(N^2) haha)
        for existing_vehicle in vehicles:
            x2 = existing_vehicle['x']
            y2 = existing_vehicle['y']
            dim_x2 = existing_vehicle['dims']['x']
            dim_y2 = existing_vehicle['dims']['y']
            if (abs(x1-x2) < (dim_x1+dim_x2)/2 and abs(y1-y2) < (dim_y1+dim_y2)/2):
                logging.debug ('place_occluding_vehicles: intersecting, dismiss')
                does_intersect = True
                break
        if not does_intersect:
            vehicles.append(vehicle)
            logging.debug ('place_occluding_vehicles: placed this one')

    return vehicles



def crop_patches (patch_dir, expand_perc, target_width, target_height):
    '''Crop patches in patch_dir directory according to their masks.
    Args:
      patch_dir:     dir with files depth-all.png, depth-car.png
      keep_src:      boolean. If true, the '-normal' and '-mask' are not deleted.
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
        expandRoiToRatio (roi, imshape, 0, ratio)
        expandRoiFloat   (roi, imshape, (expand_perc, expand_perc))

        target_shape = (target_width, target_height)

        crop_patch = patch[roi[0]:roi[2]+1, roi[1]:roi[3]+1, :]
        crop_mask  = mask [roi[0]:roi[2]+1, roi[1]:roi[3]+1]
        crop_patch = cv2.resize(crop_patch, target_shape)#, interpolation=cv2.INTER_LINEAR)
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
    logging.info ('visible perc: %0.2f' % visible_perc)
    return visible_perc


def run_patches_job (job):
    WORK_DIR = '%s-%d' % (WORK_PATCHES_DIR, os.getpid())
    if op.exists(WORK_DIR):
        shutil.rmtree(WORK_DIR)
    os.makedirs(WORK_DIR)

    logging.info ('run_patches_job started job %d' % job['i'])

    main_model  = choice(job['main_models'])
    del job['main_models']
    occl_models = job['occl_models']
    del job['occl_models']

    # place the main vehicle
    main_vehicle = main_model
    main_vehicle.update({'x': 0, 'y': 0, 'azimuth': 90})

    # place occluding vehicles
    occl_vehicles = place_occluding_vehicles (main_vehicle, occl_models)
    logging.info ('have total of %d occluding cars' % len(occl_vehicles))
    
    job['vehicles'] = [main_vehicle] + occl_vehicles

    job_path = op.join(WORK_DIR, JOB_INFO_NAME)
    with open(job_path, 'w') as f:
        f.write(json.dumps(job, indent=4))
    try:
        command = ['%s/blender' % os.getenv('BLENDER_ROOT'), '--background', '--python',
                   '%s/src/augmentation/photoSession.py' % os.getenv('CITY_PATH')]
        returncode = subprocess.call (command, shell=False)
        logging.info ('blender returned code %s' % str(returncode))
    except:
        logging.error('job for %s failed to process: %s' %
                      (job['vehicles'][0]['model_id'], traceback.format_exc()))

    # move patches-id dirs to the new home dir and number them
    scene_dir = op.join(PATCHES_HOME_DIR, job['patches_name'], 'scene-%06d' % job['i'])
    logging.debug('moving %s to %s' % (WORK_DIR, scene_dir))
    shutil.move(WORK_DIR, scene_dir)


    

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--patches_name',    type=str,   default='test')
    parser.add_argument('--logging_level',   type=int,   default=20)
    parser.add_argument('--number',          type=int,   default=1)
    parser.add_argument('--num_per_session', type=int,   default=1)
    parser.add_argument('--num_occluding',   type=int,   default=5)
    parser.add_argument('--expand_perc',     type=float, default=0.1)
    parser.add_argument('--target_width',    type=int,   default=40)
    parser.add_argument('--target_height',   type=int,   default=30)
    parser.add_argument('--render', default='SEQUENTIAL')
    parser.add_argument('--keep_src', action='store_true',
                        help='do not delete "normal" and "mask" images')
    parser.add_argument('--models_range', default='[::]', 
                        help='python style range of models in collection, e.g. "[5::2]"')
    parser.add_argument('--collection_id')
    args = parser.parse_args()

    setupLogging('log/augmentation/MakePatches.log', args.logging_level, 'w')

    # delete and recreate patches_name dir
    if args.render != 'NONE':
        if op.exists(op.join(PATCHES_HOME_DIR, args.patches_name)):
            shutil.rmtree(op.join(PATCHES_HOME_DIR, args.patches_name))
        os.makedirs(op.join(PATCHES_HOME_DIR, args.patches_name))

    cad = Cad()

    models   = cad.get_ready_models_in_collection (args.collection_id)
    diapason = Diapason (len(models), args.models_range)
    models   = diapason.filter_list(models)
    for model in models: 
        model['collection_id'] = args.collection_id
    logging.info('Using total %d models.' % len(models))

    job = {'num_per_session': args.num_per_session,
           'patches_name':    args.patches_name,
           'main_models':     models}

    # give a number to each job
    num_sessions = int(ceil(float(args.number) / args.num_per_session))
    logging.info ('num_sessions: %d' % num_sessions)
    jobs = [job.copy() for i in range(num_sessions)]
    for i,job in enumerate(jobs): 
        job['i'] = i
        job['occl_models'] = cad.get_random_ready_models (args.num_occluding)
        for occl_model in job['occl_models']:
            if 'description' in occl_model:
                del occl_model['description']  # to make it more compact


    # workhorse
    if args.render == 'SEQUENTIAL':
        for job in jobs:
            run_patches_job (job)
    elif args.render == 'PARALLEL':
        pool = multiprocessing.Pool()
        logging.info ('the pool has %d workers' % pool._processes)
        pool.map (run_patches_job, jobs)
        pool.close()
        pool.join()
    elif args.render == 'NONE':
        logging.info ('will skip rendering')
    else:
        raise Exception ('wrong args.render: %s' % args.render)

    # postprocess
    ids_f = open(op.join(PATCHES_HOME_DIR, args.patches_name, 'ids.txt'), 'w')
    vis_f = open(op.join(PATCHES_HOME_DIR, args.patches_name, 'visibility.txt'), 'w')
    roi_f = open(op.join(PATCHES_HOME_DIR, args.patches_name, 'roi.txt'), 'w')

    for scene_dir in glob(op.join(PATCHES_HOME_DIR, args.patches_name, 'scene-??????')):
        scene_name = op.basename(scene_dir)
        for patch_dir in glob(op.join(scene_dir, '??????')):
            write_visible_mask (patch_dir)
            visible_perc = get_visible_perc (patch_dir)
            patch, mask = crop_patches(patch_dir, args.expand_perc, 
                                       args.target_width, args.target_height)

            # something went wrong, probably the mask is empty
            if patch is None or mask is None: continue

            # write cropped image and visible_perc and remove the source dir
            patch_name = '%s.%s' % (op.basename(patch_dir), EXT)
            mask_name  = '%s.png' % op.basename(patch_dir)
            patch_path = op.join(scene_dir, patch_name)
            mask_path  = op.join(scene_dir, mask_name)
            cv2.imwrite(patch_path, patch)
            cv2.imwrite(mask_path, mask)
            logging.info ('wrote cropped patch: %s/%s' % (scene_name, patch_name))

            # remove patch directory, if not 'keep_src'
            if not args.keep_src:
                shutil.rmtree(patch_dir)

            # write bboxes and visibility
            ids_f.write('%s\n' % op.join(scene_name, op.basename(patch_name)))
            bbox = mask2bbox (mask)
            assert bbox is not None
            roi_str = ' '.join([str(x) for x in bbox2roi(bbox)])
            roi_f.write('%s %s\n' % (op.join(scene_name, patch_name), roi_str))
            vis_f.write('%s %f\n' % (op.join(scene_name, patch_name), visible_perc))

    ids_f.close()
    vis_f.close()
    roi_f.close()