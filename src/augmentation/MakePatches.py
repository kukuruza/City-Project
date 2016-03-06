import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import json
import logging
import numpy as np
import cv2
import glob
from math import ceil
import subprocess
import multiprocessing
import traceback
import shutil
import argparse
from learning.helperSetup import atcity, setupLogging
from learning.dbUtilities import expandRoiToRatio, expandRoiFloat, bbox2roi


COLLECTIONS_DIR  = atcity('augmentation/CAD')
RESULT_DIR       = atcity('augmentation/patches')
WORK_PATCHES_DIR = atcity('augmentation/blender/current-patch')
PATCHES_HOME_DIR = atcity('augmentation/patches')
FRAME_INFO_NAME  = 'frame_info.json'
EXT = 'jpg'  # format of output patches


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





def extract_bbox (render_png_path):
    '''Extract a single (if any) bounding box from the image
    Args:
      render_png_path:  has only one (or no) car in the image.
    Returns:
      bbox:  (x1, y1, width, height)
    '''
    if not op.exists(render_png_path):
        logging.error ('Car render image does not exist: %s' % render_png_path)
    vehicle_render = cv2.imread(render_png_path, -1)
    assert vehicle_render is not None
    assert vehicle_render.shape[2] == 4   # need alpha channel
    alpha = vehicle_render[:,:,3]
    
    # keep only vehicles with resonable bboxes
    if np.count_nonzero(alpha) == 0:   # or are there any artifacts
        return None

    # get bbox
    nnz_indices = np.argwhere(alpha)
    (y1, x1), (y2, x2) = nnz_indices.min(0), nnz_indices.max(0) + 1 
    (height, width) = y2 - y1, x2 - x1
    return (x1, y1, width, height)


def crop_patches (vehicle, expand_perc, target_width, target_height, keep_src):
    '''TL;DR: crop patches in vehicle directory according to their masks.

    We have a directory with patches and masks. 
    Their names follow convention 01blabla-normal.png and 01blabla-mask.png.
    Each '-normal' is the actual car, it is cropped according to its '-mask'.
    Each result is recorded as 01blabla.EXT.

    Args:
      vehicle:  Dir info. It's a dict with fields model_id and collection_id.
      keep_src:  boolean. If true, the '-normal' and '-mask' are not deleted.

    Returns nothing.
    '''
    patches_dir = op.join(PATCHES_HOME_DIR, vehicle['collection_id'], vehicle['model_id'])
    normal_paths = glob.glob(op.join(patches_dir, '*-normal.png'))
    logging.info ('found %d patches for model %s' % (len(normal_paths), vehicle['model_id']))

    for normal_path in normal_paths:
        try:
            name = op.splitext(op.basename(normal_path))[0][:-7]
            patches_dir = op.dirname(normal_path)
            mask_path = op.join(patches_dir, '%s-mask.png' % name)
            out_path = op.join(patches_dir, '%s.%s' % (name, EXT))

            normal = cv2.imread(normal_path)
            assert normal is not None

            bbox = extract_bbox(mask_path)
            assert bbox is not None, 'Mask is empty. Car is outside of the image.'
            roi = bbox2roi(bbox)
            ratio = float(target_height) / target_width
            imshape = (normal.shape[0], normal.shape[1])
            expandRoiToRatio (roi, imshape, 0, ratio)
            expandRoiFloat   (roi, imshape, (expand_perc, expand_perc))

            target_shape = (target_width, target_height)

            crop = normal[roi[0]:roi[2]+1, roi[1]:roi[3]+1, :]
            crop = cv2.resize(crop, target_shape)#, interpolation=cv2.INTER_LINEAR)
            cv2.imwrite(out_path, crop)

            logging.info ('cropped patch %s' % op.basename(out_path))
        except:
            logging.error('job for %s failed to process: %s' % \
                          (vehicle['model_id'], traceback.format_exc()))

        if not keep_src:
            if op.exists(normal_path): os.remove(normal_path)
            if op.exists(mask_path):   os.remove(mask_path)



def photo_session_sequential (vehicles):
    WORK_DIR = '%s-%d' % (WORK_PATCHES_DIR, os.getpid())
    if not op.exists(WORK_DIR): os.makedirs(WORK_DIR)

    for vehicle in vehicles:
        try:
            frame_info_path = op.join(WORK_DIR, FRAME_INFO_NAME)
            with open(frame_info_path, 'w') as f:
                f.write(json.dumps(vehicle, indent=4))

            command = ['%s/blender' % os.getenv('BLENDER_ROOT'), '--background',
                       '--python', '%s/src/augmentation/photoSession.py' % os.getenv('CITY_PATH')]
            returncode = subprocess.call (command, shell=False)
            logging.info ('blender returned code %s' % str(returncode))
        except:
            logging.error('job for %s failed to process: %s' % \
                          (vehicle['model_id'], traceback.format_exc()))

    if op.exists(WORK_DIR): shutil.rmtree(WORK_DIR)
        



def photo_session_parallel (vehicle):
    WORK_DIR = '%s-%d' % (WORK_PATCHES_DIR, os.getpid())
    if not op.exists(WORK_DIR): os.makedirs(WORK_DIR)

    try:
        frame_info_path = op.join(WORK_DIR, FRAME_INFO_NAME)
        with open(frame_info_path, 'w') as f:
            f.write(json.dumps(vehicle, indent=4))

        command = ['%s/blender' % os.getenv('BLENDER_ROOT'), '--background',
                   '--python', '%s/src/augmentation/photoSession.py' % os.getenv('CITY_PATH')]
        returncode = subprocess.call (command, shell=False)
        logging.info ('blender returned code %s' % str(returncode))

    except:
        logging.error('job for %s failed to process: %s' % \
                      (vehicle['model_id'], traceback.format_exc()))

    if op.exists(WORK_DIR): shutil.rmtree(WORK_DIR)



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--logging_level', type=int,   default=20)
    parser.add_argument('--number',        type=int,   default=1)
    parser.add_argument('--expand_perc',   type=float, default=0.1)
    parser.add_argument('--target_width',  type=int,   default=40)
    parser.add_argument('--target_height', type=int,   default=30)
    parser.add_argument('--render', default='SEQUENTIAL')
    parser.add_argument('--keep_src', action='store_true',
                        help='do not delete "normal" and "mask" images')
    parser.add_argument('--models_range', default='[::]', 
                        help='python style range of models in collection, e.g. "[5::2]"')
    parser.add_argument('--collection_id')
    args = parser.parse_args()

    setupLogging('log/augmentation/MakePatches.log', args.logging_level, 'w')

    collection_dir = op.join(COLLECTIONS_DIR, args.collection_id)
    #collection_dir = atcity('augmentation/CAD/7c7c2b02ad5108fe5f9082491d52810')

    collection = json.load(open( op.join(collection_dir, 'readme-blended.json') ))

    diapason = Diapason (len(collection['vehicles']), args.models_range)
    vehicles = diapason.filter_list(collection['vehicles'])
    logging.info('Total %d vehicles in the collection' % len(vehicles))

    num_per_model = int(ceil(float(args.number) / len(vehicles)))
    logging.info('Number of patches per model: %d' % num_per_model)
    for i, _ in enumerate(vehicles):
        vehicles[i]['collection_id'] = collection['collection_id']
        vehicles[i]['start_id'] = i
        vehicles[i]['num_per_model'] = num_per_model

    if args.render == 'SEQUENTIAL':
        photo_session_sequential (vehicles)
    elif args.render == 'PARALLEL':
        pool = multiprocessing.Pool()
        logging.info ('the pool has %d workers' % pool._processes)
        pool.map (photo_session_parallel, vehicles)
        pool.close()
        pool.join()
    elif args.render == 'NONE':
        logging.info ('will skip rendering')
    else:
        raise Exception ('wrong args.render: %s' % args.render)

    for vehicle in vehicles:
        crop_patches(vehicle, args.expand_perc, 
                     args.target_width, args.target_height, args.keep_src)

