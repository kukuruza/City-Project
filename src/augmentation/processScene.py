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
from helperSetup import _setupCopyDb_, setupLogging, atcity, setParamUnlessThere
from placeCars import generate_current_frame
from MonitorDatasetClient import MonitorDatasetClient
from Cad import Cad
from Camera import Camera
from Video import Video


# All rendering by blender takes place in WORK_DIR
WORK_DIR          = atcity('augmentation/blender/current-frame')
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


def extract_annotations (c, traffic, cad, camera, imagefile, monitor=None):
    '''Parse output of render and all metadata into our SQL format.
    This function knows about SQL format.
    Args:
        c:                cursor to existing db in our format
        cad:              info on the pose of every car in the frame, 
                          and its id within car collections
        camera:           dict of camera height and orientation
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
        model = cad.get_model_by_id_and_collection (vehicle['model_id'], 
                                                    vehicle['collection_id'])
        assert model is not None
        name = model['vehicle_type']

        # get vehicle angles (camera roll is assumed small and ignored)
        azimuth_view = -atan2(vehicle['y'], vehicle['x']) * 180 / pi
        yaw = (180 - vehicle['azimuth'] + azimuth_view) % 360
        height = camera.info['origin_blender']['z']
        pitch = atan(height / _get_norm_xy_(vehicle)) * 180 / pi

        # put all info together and insert into the db
        entry = (imagefile, name, bbox[0], bbox[1], bbox[2], bbox[3], yaw, pitch)
        c.execute('''INSERT INTO cars(imagefile,name,x1,y1,width,height,yaw,pitch) 
                     VALUES (?,?,?,?,?,?,?,?);''', entry)

        if monitor is not None:
            monitor.upload_vehicle({'vehicle_type': name, 'yaw': yaw, 'pitch': pitch,
                                    'width': bbox[2], 'height': bbox[3]})




def process_frame (video, camera, cad, time, num_cars, background=None, scale=1, params={}):
    ''' Full stack for one single frame (no db entries). 
    Everything about blender input and output files is hidden inside this function.
    All work is in current-frame dir.
    '''
    setParamUnlessThere (params, 'no_traffic', False)
    setParamUnlessThere (params, 'no_render',  False)
    setParamUnlessThere (params, 'no_combine', False)
    setParamUnlessThere (params, 'scale',      1.0)

    # load camera dimensions (compare it to everything for extra safety)
    width0, height0 = camera.info['camera_dims']['width'], camera.info['camera_dims']['height']

    image = None
    mask = None

    if not params['no_traffic']:
        generate_current_frame (camera, video, cad, time, num_cars, params['scale'])

    if not params['no_render']:
        # remove so that they do not exist if blender fails
        if op.exists(op.join(WORK_DIR, NORMAL_FILENAME)):
            os.remove(op.join(WORK_DIR, NORMAL_FILENAME))
        if op.exists(op.join(WORK_DIR, CARSONLY_FILENAME)):
            os.remove(op.join(WORK_DIR, CARSONLY_FILENAME))
        # render
        assert video.render_blend_file is not None
        render_blend_path = atcity(video.render_blend_file)
        command = '%s/blender %s --background --python %s/src/augmentation/renderScene.py' % \
                  (os.getenv('BLENDER_ROOT'), render_blend_path, os.getenv('CITY_PATH'))
        returncode = subprocess.call ([command], shell=True)
        logging.info ('rendering: blender returned code %s' % str(returncode))

        # check rendered
        image = cv2.imread(op.join(WORK_DIR, CARSONLY_FILENAME))
        assert image is not None
        assert image.shape == (height0, width0, 3)

        # create mask
        mask_path  = op.join(WORK_DIR, MASK_FILENAME)
        carsonly = cv2.imread( op.join(WORK_DIR, CARSONLY_FILENAME), -1 )
        assert carsonly.shape == (height0, width0, 4)  # need the alpha channel
        mask = carsonly[:,:,3] > 0

    if not params['no_combine']:
        # get background file
        assert background is not None, 'either pass no_combine or background'
        assert background.shape == (height0, width0, 3), background.shape
        cv2.imwrite (op.join(WORK_DIR, BACKGROUND_FILENAME), background)

        # remove so that they do not exist if blender fails
        if op.exists(op.join(WORK_DIR, COMBINED_FILENAME)): 
            os.remove(op.join(WORK_DIR, COMBINED_FILENAME))
        # postprocess and overlay
        assert video.combine_blend_file is not None
        combine_scene_path = atcity(video.combine_blend_file)
        command = '%s/blender %s --background --python %s/src/augmentation/combineFrame.py' % \
                  (os.getenv('BLENDER_ROOT'), combine_scene_path, os.getenv('CITY_PATH'))
        returncode = subprocess.call ([command], shell=True)
        logging.info ('combine: blender returned code %s' % str(returncode))
        assert op.exists(op.join(WORK_DIR, COMBINED_FILENAME))
        image = cv2.imread(op.join(WORK_DIR, COMBINED_FILENAME))
        assert image.shape == (height0, width0, 3)

    return (image, mask)



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


def process_video (job, args):

    # get input for this job from json
    in_db_path           = atcity(job['in_db_file'])
    out_db_path          = atcity(job['out_db_file'])
    out_image_video_file = job['out_image_video_file']
    out_mask_video_file  = job['out_mask_video_file']
    out_image_video_path = atcity(job['out_image_video_file'])
    out_mask_video_path  = atcity(job['out_mask_video_file'])

    video = Video(video_dir=job['video_dir'])
    camera = video.build_camera()
    # load camera dimensions (compare it to everything for extra safety)
    width0, height0 = camera.info['camera_dims']['width'], camera.info['camera_dims']['height']

    cad = Cad()
    cad.load(job['collection_names'])

    # upload info on parsed vehicles to the monitor server
    monitor = MonitorDatasetClient (cam_id=camera.info['cam_id'])

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
           ({'out_dataset': {in_back_video_file: out_image_video_file, 
                             in_mask_video_file: out_mask_video_file} })

    c.execute('SELECT imagefile,maskfile,time,width,height FROM images')
    image_entries = c.fetchall()
    frame_range = _parse_frame_range_arg_ (args.frame_range, len(image_entries))

    for i, (in_backfile, in_maskfile, timestamp, width, height) in enumerate(image_entries):
        logging.info ('process frame number %d' % i)
        assert (width0 == width and height0 == height)

        # background image from the video
        back = processor.imread(in_backfile)
        in_mask = processor.maskread(in_maskfile)

        if i not in frame_range:
            # skip rendering and db entry. Just rewrite the same video
            if args.record_empty_frames:
                processor.imwrite (back, in_backfile)
                processor.maskwrite (in_mask > 0, in_maskfile)
            logging.info ('skipping frame %d based on frame_range' % i)
            continue
        
        # if static_back use example background
        if not args.use_example_background:
            back = video.example_background
            assert back is not None, 'example_background not available for this video'

        # generate traffic
        elif timestamp is None:
            if video.start_time is None:
                raise Exception('timestamp is not in the .txt and not in video_info file')
            time = video.start_time + datetime.timedelta(minutes=int(float(i) / 960 * 40))
        else:
            time = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')

        # workhorse
        out_image, out_mask = process_frame(video, camera, cad, time, job['num_cars'], back)

        # write the frame to video (processor interface requires input filenames)
        assert out_image is not None and out_mask is not None
        processor.imwrite (out_image, in_backfile)
        processor.maskwrite (out_mask, in_maskfile)

        # update the filename in database
        out_imagefile = op.join(op.splitext(out_image_video_file)[0], op.basename(in_backfile))
        out_maskfile  = op.join(op.splitext(out_mask_video_file)[0], op.basename(in_maskfile))
        c.execute('UPDATE images SET imagefile=?, maskfile=? WHERE imagefile=?', 
                    (out_imagefile, out_maskfile, in_backfile))

        frame_info = json.load(open( op.join(WORK_DIR, TRAFFIC_FILENAME) ))
        extract_annotations (c, frame_info, cad, camera, out_imagefile, monitor)

    conn.commit()
    conn.close()



