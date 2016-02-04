import sys, os, os.path as op
from glob import glob
from time import sleep, time
import json
import numpy as np
import cv2
import argparse
from math import pi, atan, atan2, pow, sqrt

sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/backend'))
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/monitor'))
import logging
import sqlite3
import datetime
import helperSetup
import helperDb
import helperImg
import utilities
import subprocess
import shutil
from video2dataset import video2dataset
from helperImg import ProcessorVideo
from helperSetup import _setupCopyDb_, setupLogging, atcity
from placeCars import generate_current_frame
from MonitorDatasetClient import MonitorDatasetClient

# All rendering by blender takes place in WORK_DIR
WORK_DIR          = op.join(os.getenv('CITY_DATA_PATH'), 'augmentation/render/current-frame')
BACKGROUND_FILENAME = 'background.png'
NORMAL_FILENAME     = 'normal.png'
CARSONLY_FILENAME   = 'cars-only.png'
COMBINED_FILENAME   = 'out.png'
MASK_FILENAME       = 'mask.png'
TRAFFIC_FILENAME    = 'traffic.json'

assert os.getenv('BLENDER_ROOT') is not None, \
    'export BLENDER_ROOT with path to blender binary as environmental variable'


def _sq_(x): return pow(x,2)

def _get_norm_xy_(a): return sqrt(_sq_(a['x']) + _sq_(a['y']))

def image2ghost (image_path, background_path, out_path):
    '''Subtract background from image and save as the ghost frame
    '''
    img  = cv2.imread(image_path)
    back = cv2.imread(background_path)
    ghost = img / 2 + 128 - back / 2
    np.imwrite(ghost, out_path)


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


def _find_carmodel_by_id_ (collection, model_id):
    # TODO: replace sequential search with an elasticsearch index
    for carmodel in collection['vehicles']:
        if carmodel['model_id'] == model_id:
            return carmodel
    return None


def extract_annotations (c, traffic, collections_dict, camera_pose, imagefile, monitor=None):
    '''Parse output of render and all metadata into our SQL format.
    This function knows about SQL format.
    Args:
        c:                cursor to existing db in our format
        traffic:          info on the pose of every car in the frame, 
                          and its id within car collections
        collections_dict: dict of collection_id -> collection
        camera_pose:      dict of camera height and orientation
        imagefile:        database entry
        monitor:          MonitorDatasetClient object for uploading vehicle info
    Returns:
        nothing
    '''
    for i,vehicle in enumerate(traffic['vehicles']):

        # get bbox
        render_png_path = op.join (WORK_DIR, 'vehicle-%d.png' % i)
        bbox = extract_bbox (render_png_path)
        if bbox is None: continue

        # get vehicle "name" (that is, type)
        collection = collections_dict[vehicle['collection_id']]
        carmodel = _find_carmodel_by_id_ (collection, vehicle['model_id'])
        assert carmodel is not None
        name = carmodel['vehicle_type']

        # get vehicle angles (camera roll is assumed small and ignored)
        azimuth_view = -atan2(vehicle['y'], vehicle['x']) * 180 / pi
        yaw = 180 - vehicle['azimuth'] + azimuth_view
        pitch = atan(camera_pose['height'] / _get_norm_xy_(vehicle)) * 180 / pi

        # put all info together and insert into the db
        entry = (imagefile, name, bbox[0], bbox[1], bbox[2], bbox[3], yaw, pitch)
        c.execute('''INSERT INTO cars(imagefile,name,x1,y1,width,height,yaw,pitch) 
                     VALUES (?,?,?,?,?,?,?,?);''', entry)

        if monitor is not None:
            monitor.upload_vehicle({'vehicle_type': name, 'yaw': yaw, 'pitch': pitch,
                                    'width': bbox[2], 'height': bbox[3]})



def process_current_frame (args):
    ''' Full stack for one single frame (no db entries). All work is in current-frame dir.
        Background file must be in current-frame dir.
        'Now' is taken as timestamp.
    '''
    # get input for this job from json
    job_info = json.load(open(args.job_path))
    render_scene_path    = op.join(args.relpath, job_info['render_scene_file'])
    combine_scene_path   = op.join(args.relpath, job_info['combine_scene_file'])

    # load camera dimensions (compare it to everything for extra safety)
    camera_info = json.load(open( op.join(os.getenv('CITY_DATA_PATH'), job_info['camera_file']) ))
    width0, height0 = camera_info['camera_dims']['width'], camera_info['camera_dims']['height']

    if not args.no_traffic:
        # generate traffic
        timestamp = datetime.datetime.now()
        generate_current_frame (job_info['collections'],
                                job_info['camera_file'], job_info['i_googlemap'], timestamp, 
                                job_info['num_cars'], job_info['weather'])

    if not args.no_render:
        # remove so that they do not exist if blender fails
        if op.exists(op.join(WORK_DIR, NORMAL_FILENAME)):
            os.remove(op.join(WORK_DIR, NORMAL_FILENAME))
        if op.exists(op.join(WORK_DIR, CARSONLY_FILENAME)):
            os.remove(op.join(WORK_DIR, CARSONLY_FILENAME))
        # render
        command = '%s/blender %s --background --python %s/src/augmentation/renderScene.py' % \
                  (os.getenv('BLENDER_ROOT'), render_scene_path, os.getenv('CITY_PATH'))
        returncode = subprocess.call ([command], shell=True)
        logging.info ('rendering: blender returned code %s' % str(returncode))

    if not args.no_combine:
        # create mask
        mask_path  = op.join(WORK_DIR, MASK_FILENAME)
        carsonly = cv2.imread( op.join(WORK_DIR, CARSONLY_FILENAME), -1 )
        assert carsonly.shape[2] == 4   # need the alpha channel
        assert (width0 == carsonly.shape[1] and height0 == carsonly.shape[0])
        mask = np.array(carsonly[:,:,3] > 0).astype(np.uint8) * 255
        cv2.imwrite (mask_path, mask)

        # remove so that they do not exist if blender fails
        if op.exists(op.join(WORK_DIR, COMBINED_FILENAME)): 
            os.remove(op.join(WORK_DIR, COMBINED_FILENAME))
        # postprocess and overlay
        command = '%s/blender %s --background --python %s/src/augmentation/combineFrame.py' % \
                  (os.getenv('BLENDER_ROOT'), combine_scene_path, os.getenv('CITY_PATH'))
        returncode = subprocess.call ([command], shell=True)
        logging.info ('combine: blender returned code %s' % str(returncode))
        assert op.exists(op.join(WORK_DIR, COMBINED_FILENAME))
        image = cv2.imread(op.join(WORK_DIR, COMBINED_FILENAME))
        assert (width0 == image.shape[1] and height0 == image.shape[0])



def _parse_frame_range_arg_ (range_str, length):
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
    logging.debug ('parsed range_str %s into range %s' % (range_str, range_py))
    return range_py


def process_video (args):

    # get input for this job from json
    job_info = json.load(open(args.job_path))
    in_db_path           = op.join(args.relpath, job_info['in_db_file'])
    out_db_path          = op.join(args.relpath, job_info['out_db_file'])
    out_image_video_file = job_info['out_image_video_file']
    out_mask_video_file  = job_info['out_mask_video_file']
    out_image_video_path = op.join(args.relpath, job_info['out_image_video_file'])
    out_mask_video_path  = op.join(args.relpath, job_info['out_mask_video_file'])
    render_scene_path    = op.join(args.relpath, job_info['render_scene_file'])
    combine_scene_path   = op.join(args.relpath, job_info['combine_scene_file'])

    # load camera dimensions (compare it to everything for extra safety)
    camera_info = json.load(open( op.join(os.getenv('CITY_DATA_PATH'), job_info['camera_file']) ))
    width0, height0 = camera_info['camera_dims']['width'], camera_info['camera_dims']['height']
    # load camera pose (deduce objects angles from it)
    camera_pose = camera_info['camera_pose']

    # upload inof on parsed vehicles to the monitor server
    monitor = MonitorDatasetClient (cam_id=camera_info['cam_id'])

    # load vehicle models collections
    collections_dict = {}
    for collection_id in job_info['collections']:
        collection_path = atcity(op.join('augmentation/CAD', collection_id, 'readme.json'))
        collections_dict[collection_id] = json.load(open(collection_path))

    # copy input db to output and open it
    _setupCopyDb_ (in_db_path, out_db_path)
    conn = sqlite3.connect (out_db_path)
    c = conn.cursor()

    # remove video if exist
    if op.exists(out_image_video_path): os.remove(out_image_video_path)
    if op.exists(out_mask_video_path):  os.remove(out_mask_video_path)

    # value for 'src' field in db
    name = op.basename(op.splitext(out_db_path)[0])
    logging.info ('new src name: %s' %  name)

    # names of in and out videos
    c.execute('SELECT imagefile,maskfile FROM images')
    some_image_entry = c.fetchone()
    in_back_video_file  = op.dirname(some_image_entry[0]) + '.avi'
    in_mask_video_file  = op.dirname(some_image_entry[1]) + '.avi'
    logging.info ('in back_video_file:   %s' % in_back_video_file)
    logging.info ('in mask_video_file:   %s' % in_mask_video_file)
    logging.info ('out image_video_file: %s' % out_image_video_file)
    logging.info ('out mask_video_file:  %s' % out_mask_video_file)

    processor = ProcessorVideo \
           ({'relpath': args.relpath,
             'out_dataset': {in_back_video_file: out_image_video_file, 
                             in_mask_video_file: out_mask_video_file} })

    c.execute('SELECT imagefile,maskfile,time,width,height FROM images')
    image_emtries = c.fetchall()
    frame_range = _parse_frame_range_arg_ (args.frame_range, len(image_emtries))

    for i, (in_backfile, in_maskfile, timestamp, width, height) in enumerate(image_emtries):
        logging.info ('process frame number %d' % i)
        assert (width0 == width and height0 == height)

        # background image from the video
        back = processor.imread(in_backfile)
        in_mask = processor.maskread(in_maskfile)

        # skip rendering and db entry. Just rewrite the same video
        if i not in frame_range:
            if args.record_empty_frames:
                processor.imwrite (back, in_backfile)
                processor.maskwrite (in_mask > 0, in_maskfile)
            logging.info ('skipping frame %d based on frame_range' % i)
            continue
        
        # check that the background is already there (if static_back) or write it down there
        if not args.static_back:
            cv2.imwrite (op.join(WORK_DIR, BACKGROUND_FILENAME), back)
        assert op.exists(op.join(WORK_DIR, BACKGROUND_FILENAME))

        # generate traffic
        if timestamp is None:
            time = datetime.datetime.strptime(args.start_time, '%Y-%m-%d %H:%M:%S.%f')
            time += datetime.timedelta(minutes=int(float(i) / 960 * 40))
        else:
            time = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
        generate_current_frame (job_info['collections'],
                                job_info['camera_file'], job_info['i_googlemap'], time, 
                                job_info['num_cars'], job_info['weather'], args.scale)

        # remove so that they do not exist if blender fails
        if op.exists(op.join(WORK_DIR, NORMAL_FILENAME)):
            os.remove(op.join(WORK_DIR, NORMAL_FILENAME))
        if op.exists(op.join(WORK_DIR, CARSONLY_FILENAME)):
            os.remove(op.join(WORK_DIR, CARSONLY_FILENAME))
        # render
        command = '%s/blender %s --background --python %s/src/augmentation/renderScene.py' % \
                  (os.getenv('BLENDER_ROOT'), render_scene_path, os.getenv('CITY_PATH'))
        returncode = subprocess.call ([command], shell=True)
        logging.info ('rendering: blender returned code %s' % str(returncode))

        # create mask
        mask_path  = op.join(WORK_DIR, MASK_FILENAME)
        carsonly = cv2.imread( op.join(WORK_DIR, CARSONLY_FILENAME), -1 )
        assert carsonly.shape[2] == 4   # need the alpha channel
        assert (width0 == carsonly.shape[1] and height0 == carsonly.shape[0])
        out_mask = carsonly[:,:,3] > 0

        # remove so that they do not exist if blender fails
        if op.exists(op.join(WORK_DIR, COMBINED_FILENAME)): 
            os.remove(op.join(WORK_DIR, COMBINED_FILENAME))
        # postprocess and overlay
        command = '%s/blender %s --background --python %s/src/augmentation/combineFrame.py' % \
                  (os.getenv('BLENDER_ROOT'), combine_scene_path, os.getenv('CITY_PATH'))
        returncode = subprocess.call ([command], shell=True)
        logging.info ('combine: blender returned code %s' % str(returncode))
        out_image = cv2.imread(op.join(WORK_DIR, COMBINED_FILENAME))
        assert (width0 == out_image.shape[1] and height0 == out_image.shape[0])

        # write the frame to video (processor interface requires input filenames)
        processor.imwrite (out_image, in_backfile)
        processor.maskwrite (out_mask, in_maskfile)

        # update the filename in database
        out_imagefile = op.join(op.splitext(out_image_video_file)[0], op.basename(in_backfile))
        out_maskfile  = op.join(op.splitext(out_mask_video_file)[0], op.basename(in_maskfile))
        c.execute('UPDATE images SET imagefile=?, maskfile=? WHERE imagefile=?', 
                    (out_imagefile, out_maskfile, in_backfile))

        frame_info = json.load(open( op.join(WORK_DIR, TRAFFIC_FILENAME) ))
        extract_annotations (c, frame_info, collections_dict, camera_pose, out_imagefile, monitor)

    conn.commit()
    conn.close()

    

if __name__ == "__main__":

    setupLogging('log/augmentation/processScene.log', logging.INFO, 'a')

    parser = argparse.ArgumentParser()
    parser.add_argument('--no_traffic', action='store_true')
    parser.add_argument('--no_render',  action='store_true')
    parser.add_argument('--no_combine', action='store_true')
    parser.add_argument('--static_back', action='store_true')
    parser.add_argument('--record_empty_frames', action='store_true')
    parser.add_argument('--frame_range', nargs='?', default='[::]', 
                        help='python style ranges, e.g. "[5::2]"')
    parser.add_argument('--start_time', nargs='?', default='2014-01-13 09:30:00.000') # temporary
    parser.add_argument('--scale', nargs='?', default=1, type=float)  # why all cars are too big?
    parser.add_argument('--relpath', nargs='?', default=os.getenv('CITY_DATA_PATH'))
    parser.add_argument('--job_path')
    args = parser.parse_args()

    #process_current_frame(args)
    process_video(args)

