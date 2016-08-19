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
from augmentation.Cad import Cad

WORK_PATCHES_DIR = atcity('augmentation/blender/current-patch')
JOB_INFO_NAME    = 'job_info.json'
OUT_INFO_NAME    = 'out_info.json'

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
        logging.info ('Diapason parsed range_str %s into range of length %d' % 
                      (range_str, len(range_py)))
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
    scene_dir = atcity(op.join(job['out_dir'], 'scene-%06d' % job['i']))
    logging.debug('moving %s to %s' % (WORK_DIR, scene_dir))
    shutil.move(WORK_DIR, scene_dir)


    

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--out_dir', default='augmentation/patches/test')
    parser.add_argument('--logging_level',   type=int,   default=20)
    parser.add_argument('--number',          type=int,   default=4,
                        help='total number of pathces to generate')
    parser.add_argument('--num_per_session', type=int,   default=2)
    parser.add_argument('--num_occluding',   type=int,   default=5)
    parser.add_argument('--render', default='SEQUENTIAL')
    parser.add_argument('--save_blender', action='store_true',
                        help='save .blend render file')
    parser.add_argument('--models_range', default='[::]', 
                        help='python style range of models in collection, e.g. "[5::2]"')
    parser.add_argument('--collection_id', required=False,
                        help='if left empty, use all collections')

    args = parser.parse_args()

    setupLogging('log/augmentation/MakePatches.log', args.logging_level, 'w')

    # delete and recreate out_dir
    if op.exists(atcity(args.out_dir)):
        shutil.rmtree(atcity(args.out_dir))
    os.makedirs(atcity(args.out_dir))

    cad = Cad()

    if args.collection_id is None:
        logging.info ('using get_all_ready_models')
        main_models = cad.get_all_ready_models()
    else:
        logging.info ('using get_ready_models_in_collection')
        main_models = cad.get_ready_models_in_collection(args.collection_id)

    diapason = Diapason (len(main_models), args.models_range)
    main_models   = diapason.filter_list(main_models)
    logging.info('Using total %d models.' % len(main_models))

    job = {'num_per_session': args.num_per_session,
           'out_dir':         args.out_dir,
           'main_models':     main_models,
           'save_blender':    args.save_blender}

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
    else:
        raise Exception ('wrong args.render: %s' % args.render)
