import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
from glob import glob
from time import sleep, time
import json
import numpy as np
import cv2
import argparse
import logging
import sqlite3
import subprocess
import multiprocessing
import shutil
from datetime import datetime, timedelta
from math import pi, atan, atan2, pow, sqrt, ceil

from learning.dbUtilities import *
from learning.helperImg import ProcessorVideo
from learning.helperSetup import _setupCopyDb_, setupLogging, atcity
from learning.helperSetup import setParamUnlessThere, assertParamIsThere
from learning.helperDb import createDb
from placeCars import generate_current_frame
from learning.video2dataset import make_dataset
from monitor.MonitorDatasetClient import MonitorDatasetClient
from Cad import Cad
from Camera import Camera
from Video import Video
from colorCorrection import color_correction, unsharp_mask


WORK_RENDER_DIR     = atcity('augmentation/blender/current-frame')
RENDERED_FILENAME   = 'render.png'
CARSONLY_FILENAME   = 'cars-only.png'
BACKGROUND_FILENAME = 'background.png'
COMBINED_FILENAME   = 'out.png'
MASK_FILENAME       = 'mask.png'
TRAFFIC_FILENAME    = 'traffic.json'
CORRECTION_FILENAME = 'color-correction.json'
FNULL = open(op.join(os.getenv('CITY_PATH'), 'log/augmentation/blender.log'), 'w')

assert os.getenv('BLENDER_ROOT') is not None, \
    'export BLENDER_ROOT with path to blender binary as environmental variable'


def _sq(x): return pow(x,2)

def _get_norm_xy_(a): return sqrt(_sq(a['x']) + _sq(a['y']))


def extract_bbox (depth):
  '''Extract a single (if any) bounding box from the image
  Args:
    depth: has only one (or no) car in the image.
  Returns:
    bbox:  (x1, y1, width, height)
  '''
  # keep only vehicles with resonable bboxes
  if np.count_nonzero(depth < 255) == 0:   # or are there any artifacts
    return None

  # get bbox
  nnz_indices = np.argwhere(depth < 255)
  (y1, x1), (y2, x2) = nnz_indices.min(0), nnz_indices.max(0) + 1 
  (height, width) = y2 - y1, x2 - x1
  return (x1, y1, width, height)


def extract_annotations (work_dir, c, cad, camera, imagefile, monitor=None):
  '''Parse output of render and all metadata into our SQL format.
  This function knows about SQL format.
  Args:
      work_dir:         path with depth-s
      c:                cursor to existing db in our format
      cad:              info on the pose of every car in the frame, 
                        and its id within car collections
      camera:           dict of camera height and orientation
      imagefile:        database entry
      monitor:          MonitorDatasetClient object for uploading vehicle info
  Returns:
      nothing
  '''
  traffic = json.load(open( op.join(work_dir, TRAFFIC_FILENAME) ))

  for i,vehicle in enumerate(traffic['vehicles']):

    # get bbox
    depth_path = op.join (work_dir, 'depth-%03d.png' % i)
    assert op.exists(depth_path), depth_path
    depth = cv2.imread(depth_path, 0)
    bbox = extract_bbox (depth)
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

    # get vehicle visibility
    vis = vehicle['visibility']

    # put all info together and insert into the db
    entry = (imagefile, name, bbox[0], bbox[1], bbox[2], bbox[3], yaw, pitch, vis)
    c.execute('''INSERT INTO cars(imagefile,name,x1,y1,width,height,yaw,pitch,score)
                 VALUES (?,?,?,?,?,?,?,?,?);''', entry)

    if monitor is not None:
      monitor.upload_vehicle({'vehicle_type': name, 'yaw': yaw, 'pitch': pitch,
                              'width': bbox[2], 'height': bbox[3]})



def _get_visible_perc (patch_dir):
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




def _get_masks (patch_dir, frame_info):
  ''' patch_dir contains "depth-all.png" and a bunch of "depth-XXX.png"
  Compare them and make a final mask of each car.
  This function changes 'frame_info'
  '''

  # read depth-all
  depth_all_path = op.join(patch_dir, 'depth-all.png')
  depth_all = cv2.imread(depth_all_path, 0)
  assert depth_all is not None, depth_all_path
  assert depth_all.dtype == np.uint8

  # mask for all cars
  mask_all = np.zeros(depth_all.shape, dtype=np.uint8)

  for i in range(len(frame_info['vehicles'])):
    # read depth-XXX and check
    depth_car_path = op.join(patch_dir, 'depth-%03d.png' % i)
    depth_car = cv2.imread(depth_car_path, 0)
    assert depth_car is not None, depth_car_path
    assert depth_car.dtype == np.uint8
    assert depth_car.shape == depth_all.shape

    # get mask of the car
    mask_full = depth_car < 255
    mask_visible = np.bitwise_and (mask_full, depth_car == depth_all)
    color = 255 * i / len(frame_info['vehicles'])
    mask_all += mask_visible.astype(np.uint8) * color
    #cv2.imshow('mask_full', mask_full.astype(np.uint8) * 255)
    #cv2.imshow('mask_visible', mask_visible.astype(np.uint8) * 255)
    #cv2.imshow('mask_all', mask_all)
    #cv2.waitKey(-1)

    # find the visibility percentage of the car
    if np.count_nonzero(mask_full) == 0:
        visibility = 0
    else:
        visibility = float(np.count_nonzero(mask_visible)) \
                   / float(np.count_nonzero(mask_full))
    frame_info['vehicles'][i]['visibility'] = visibility

  # disabled a mask output segmented by car. Returning a binary mask now.
  #return mask_all
  return mask_all > 0



def render_frame (video, camera, traffic):
  ''' Write down traffci file for blender and run blender with renderScene.py 
  All work is in current-frame dir.
  '''
  WORK_DIR = '%s-%d' % (WORK_RENDER_DIR, os.getpid())
  setParamUnlessThere (traffic, 'save_blender_files', False)
  setParamUnlessThere (traffic, 'render_individual_cars', True)
  unsharp_mask_params = {'radius': 4.7, 'threshold': 23, 'amount': 1}

  # load camera dimensions (compare it to everything for extra safety)
  width0  = camera.info['camera_dims']['width']
  height0 = camera.info['camera_dims']['height']
  logging.debug ('camera width,height: %d,%d' % (width0, height0))

  image = None
  mask = None

  # pass traffic info to blender
  traffic['scale'] = camera.info['scale']
  traffic_path = op.join(WORK_DIR, TRAFFIC_FILENAME)
  if not op.exists(op.dirname(traffic_path)):
    os.makedirs(op.dirname(traffic_path))
  with open(traffic_path, 'w') as f:
    f.write(json.dumps(traffic, indent=4))

  # remove so that they do not exist if blender fails
  if op.exists(op.join(WORK_DIR, RENDERED_FILENAME)):
      os.remove(op.join(WORK_DIR, RENDERED_FILENAME))
  if op.exists(op.join(WORK_DIR, 'depth-all.png')):
      os.remove(op.join(WORK_DIR, 'depth-all.png'))
  # render
  assert video.render_blend_file is not None
  render_blend_path = atcity(video.render_blend_file)
  command = ['%s/blender' % os.getenv('BLENDER_ROOT'), render_blend_path, 
             '--background', '--python',
             '%s/src/augmentation/renderScene.py' % os.getenv('CITY_PATH')]
  returncode = subprocess.call (command, shell=False, stdout=FNULL, stderr=FNULL)
  logging.info ('rendering: blender returned code %s' % str(returncode))

  # check and sharpen rendered
  rendered_filepath = op.join(WORK_DIR, RENDERED_FILENAME)
  image = cv2.imread(rendered_filepath, -1)
  assert image is not None
  assert image.shape == (height0, width0, 4), image.shape
  image = unsharp_mask (image, unsharp_mask_params)
  cv2.imwrite (rendered_filepath, image)

  # check and sharpen cars-only
  carsonly_filepath = op.join(WORK_DIR, CARSONLY_FILENAME)
  image = cv2.imread(carsonly_filepath, -1)
  assert image is not None
  assert image.shape == (height0, width0, 4), image.shape
  image = unsharp_mask (image, unsharp_mask_params)
  shutil.move (carsonly_filepath, op.join(WORK_DIR, 'unsharpened.png'))
  cv2.imwrite (carsonly_filepath, image)

  # create mask
  mask = _get_masks (WORK_DIR, traffic)
  # TODO: visibility is returned via traffic file, NOT straightforward
  with open(traffic_path, 'w') as f:
      f.write(json.dumps(traffic, indent=4))

  # correction_path = op.join(WORK_DIR, CORRECTION_FILENAME)
  # if op.exists(correction_path): os.remove(correction_path)
  # if not params['no_correction']:
  #     correction_info = color_correction (video.example_background, background)
  #     with open(correction_path, 'w') as f:
  #         f.write(json.dumps(correction_info, indent=4))

  return image, mask


def combine_frame (background, video, camera):
  ''' Overlay image onto background '''
  jpg_qual = 40

  WORK_DIR = '%s-%d' % (WORK_RENDER_DIR, os.getpid())

  # load camera dimensions (compare it to everything for extra safety)
  width0  = camera.info['camera_dims']['width']
  height0 = camera.info['camera_dims']['height']

  # get background file
  assert background is not None
  assert background.shape == (height0, width0, 3), background.shape
  cv2.imwrite (op.join(WORK_DIR, BACKGROUND_FILENAME), background)

  # remove previous result so that there is an error if blender fails
  if op.exists(op.join(WORK_DIR, COMBINED_FILENAME)): 
      os.remove(op.join(WORK_DIR, COMBINED_FILENAME))

  # overlay
  assert video.combine_blend_file is not None
  combine_scene_path = atcity(video.combine_blend_file)
  command = ['%s/blender' % os.getenv('BLENDER_ROOT'), combine_scene_path,
             '--background', '--python',
             '%s/src/augmentation/combineScene.py' % os.getenv('CITY_PATH')]
  returncode = subprocess.call (command, shell=False, stdout=FNULL, stderr=FNULL)
  logging.info ('combine: blender returned code %s' % str(returncode))
  combined_filepath = op.join(WORK_DIR, COMBINED_FILENAME)
  assert op.exists(combined_filepath), combined_filepath
  image = cv2.imread(combined_filepath)
  assert image.shape == (height0, width0, 3), image.shape

  # reencode to match jpeg quality
  shutil.move (combined_filepath, op.join(WORK_DIR, 'uncompressed.png'))
  _, ajpg = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, jpg_qual])
  image = cv2.imdecode(ajpg, cv2.CV_LOAD_IMAGE_COLOR)
  cv2.imwrite (combined_filepath, image)

  return image


class Diapason:

  def _parse_range_str_ (self, range_str, length):
    '''Parses string into python range
    '''
    assert isinstance(range_str, basestring)
    # remove [ ] around the range
    if len(range_str) >= 2 and range_str[0] == '[' and range_str[-1] == ']':
        range_str = range_str[1:-1]
    # split into three elements start,end,step. Assign step=1 if missing
    arr = range_str.split(':')
    assert len(arr) == 2 or len(arr) == 3, 'need 1 or 2 columns ":" in range str'
    if len(arr) == 2: arr.append('1')
    if arr[0] == '': arr[0] = '0'
    if arr[1] == '': arr[1] = str(length)
    if arr[2] == '': arr[2] = '1'
    start = int(arr[0])
    end   = int(arr[1])
    step  = int(arr[2])
    range_py = range(start, end, step)
    logging.debug ('Diapason parsed range_str %s into range of length %d' % 
                    (range_str, len(range_py)))
    return range_py

  def __init__ (self, length, frame_range_str):
    self.frame_range = self._parse_range_str_ (frame_range_str, length)

  def intersect (self, diapason):
    interset = set(self.frame_range).intersection(diapason.frame_range)
    self.frame_range = sorted(interset)
    logging.info ('Diapason intersection has %d frames' % len(self.frame_range))
    logging.debug ('Diapason intersection is range %s' % self.frame_range)
    return self

  def frame_range_as_chunks (self, chunk_size):
    ''' Cutting frame_range into chunks for parallel execution '''
    chunks = []
    chunk_num = int(ceil( len(self.frame_range) / float(chunk_size) ))
    for i in range(chunk_num):
      r = self.frame_range[i*chunk_size : min((i+1)*chunk_size, len(self.frame_range))]
      chunks.append(r)
    return chunks


def _get_time (video, timestamp, frame_id):
  if timestamp is None:
    assert video.start_time is not None, 'no time in .db or in video_info file'
    time = video.start_time + timedelta(minutes=int(float(frame_id) / 960 * 40))
  else:
    time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
  return time


def generate_video_traffic (job):
  ''' Generate traffic file for the whole video for possible further use 
  Args:
    job - the same as for process_video
  '''

  assertParamIsThere  (job, 'out_video_dir')
  setParamUnlessThere (job, 'frame_range', '[::]')
  assertParamIsThere  (job, 'video_dir')

  video = Video(video_dir=job['video_dir'])
  camera = video.build_camera()

  in_db_file = create_in_db(job)   # creates in_db_file if necessary
  c_in = sqlite3.connect(atcity(in_db_file)).cursor()
  c_in.execute('SELECT time FROM images')
  timestamps = c_in.fetchall()

  cad = Cad()
  cad.load(job['collection_names'])

  diapason = Diapason (len(timestamps), job['frame_range']).intersect(
             Diapason (len(timestamps), video.info['frame_range']) )
  
  traffic_seq = []

  for frame_id in diapason.frame_range:
    logging.info ('generating traffic for frame %d' % frame_id)
    timestamp = timestamps[frame_id][0]
    time = _get_time (video, timestamp, frame_id)
    traffic = generate_current_frame(camera, video, cad, time, job['num_cars'])
    traffic['frame_id'] = frame_id  # for validating
    traffic_seq.append(traffic)

  return traffic_seq




def mywrapper((video, camera, traffic, back, job)):
  ''' wrapper for parallel processing. Argument is an element of frame_jobs 
  '''
  WORK_DIR = '%s-%d' % (WORK_RENDER_DIR, os.getpid())
  if not op.exists(WORK_DIR): os.makedirs(WORK_DIR)

  _, out_mask = render_frame(video, camera, traffic)
  out_image = combine_frame (back, video, camera)

  return out_image, out_mask, WORK_DIR



def process_video (job):

  # for checking timeout
  start_time = datetime.now()

  assertParamIsThere  (job, 'video_dir')
  video = Video(video_dir=job['video_dir'])
  camera = video.build_camera()

  # some parameters
  assertParamIsThere  (job, 'traffic_file')
  setParamUnlessThere (job, 'save_blender_files', False)
  setParamUnlessThere (job, 'out_video_dir', 
      op.join('augmentation/video', 'cam%s' % camera.info['cam_id'], video.info['video_name']))
  setParamUnlessThere (job, 'no_annotations', False)
  setParamUnlessThere (job, 'timeout', 1000000000)
  setParamUnlessThere (job, 'frame_range', '[::]')
  in_db_file = create_in_db(job)   # creates in_db_file if necessary

  # get input for this job from json
  out_image_video_file = op.join(job['out_video_dir'], 'image.avi')
  out_mask_video_file  = op.join(job['out_video_dir'], 'mask.avi')
  if job['no_annotations']: job['render_individual_cars'] = False

  # load camera dimensions (compare it to everything for extra safety)
  width0  = camera.info['camera_dims']['width']
  height0 = camera.info['camera_dims']['height']

  cad = Cad()
  cad.load(job['collection_names'])

  # upload info on parsed vehicles to the monitor server
  monitor = MonitorDatasetClient (cam_id=camera.info['cam_id'])

  # open in_db and create and open a new out_db
  out_db_path = atcity(op.join(job['out_video_dir'], 'traffic.db'))
  if op.exists(out_db_path): os.remove(out_db_path)
  conn_in  = sqlite3.connect(atcity(in_db_file))
  conn_out = sqlite3.connect(out_db_path)
  # TODO: make createDb take cursor
  createDb(conn_out)
  c_in  = conn_in.cursor()
  c_out = conn_out.cursor()

  # remove video if exist
  if not op.exists(atcity(job['out_video_dir'])): os.makedirs(atcity(job['out_video_dir']))
  if op.exists(atcity(out_image_video_file)): os.remove(atcity(out_image_video_file))
  if op.exists(atcity(out_mask_video_file)):  os.remove(atcity(out_mask_video_file))

  # value for 'src' field in db
  name = op.basename(op.splitext(out_db_path)[0])
  logging.info ('new src name: %s' %  name)

  # names of in and out videos
  c_in.execute('SELECT imagefile,maskfile FROM images')
  some_image_entry = c_in.fetchone()
  assert some_image_entry is not None
  in_back_video_file  = op.dirname(some_image_entry[0]) + '.avi'
  in_mask_video_file  = op.dirname(some_image_entry[1]) + '.avi'
  logging.info ('in back_video_file:   %s' % in_back_video_file)
  logging.info ('in mask_video_file:   %s' % in_mask_video_file)
  logging.info ('out image_video_file: %s' % out_image_video_file)
  logging.info ('out mask_video_file:  %s' % out_mask_video_file)

  processor = ProcessorVideo \
         ({'out_dataset': {in_back_video_file: out_image_video_file, 
                           in_mask_video_file: out_mask_video_file} })

  c_in.execute('SELECT imagefile,maskfile,time,width,height FROM images')
  image_entries = c_in.fetchall()

  diapason = Diapason (len(image_entries), job['frame_range']).intersect(
             Diapason (len(image_entries), video.info['frame_range']) )

  # traffic is pregenerated now
  traffic_seq = json.load(open(atcity(job['traffic_file'])))
  
  pool = multiprocessing.Pool()

  # will only write meaningful frames
  i_out = 0

  # each frame_range chunk is processed in parallel
  for frame_range in diapason.frame_range_as_chunks(pool._processes):
    logging.info ('chunk of frames %d to %d' % (frame_range[0], frame_range[-1]))

    # quit, if reached the timeout
    time_passed = datetime.now() - start_time
    logging.info ('passed: %s' % time_passed)
    if (time_passed.total_seconds() > job['timeout'] * 60):
      logging.warning('reached timeout %d. Passed %s' % (job['timeout'], time_passed))
      break

    # collect frame jobs
    frame_jobs = []
    for i, frame_id in enumerate(frame_range):

      (in_backfile, in_maskfile, timestamp, width, height) = image_entries[frame_id]
      assert (width0 == width and height0 == height), (width0, width, height0, height)
      logging.info ('process frame number %d' % frame_id)

      back = processor.imread(in_backfile)
      _ = processor.maskread(in_maskfile)
      time = _get_time (video, timestamp, frame_id)

      traffic = traffic_seq.pop(0)
      assert traffic['frame_id'] == frame_id, \
          '%d vs %d' % (traffic['frame_id'], frame_id)
      traffic['save_blender_files'] = job['save_blender_files']

      # sum all up into one job
      frame_jobs.append((video, camera, traffic, back, job))

    for i, (out_image, out_mask, work_dir) in enumerate(pool.imap(mywrapper, frame_jobs)):
      frame_id = frame_range[i]
      print 'my frame_id: %d' % frame_id

      # get the same info again
      (in_backfile, in_maskfile, timestamp, width, height) = image_entries[frame_id]
      time = _get_time (video, timestamp, frame_id)

      # write the frame to video (processor interface requires input filenames)
      assert out_image is not None and out_mask is not None
      processor.imwrite (out_image, in_backfile)
      processor.maskwrite (out_mask, in_maskfile)

      # update out database
      out_imagefile = op.join(op.splitext(out_image_video_file)[0], '%06d' % i_out)
      out_maskfile  = op.join(op.splitext(out_mask_video_file)[0], '%06d' % i_out)
      src = 'generated from %s' % in_back_video_file
      c_out.execute ('INSERT INTO images(imagefile,maskfile,src,width,height,time) '
                     'VALUES (?,?,?,?,?,?)',
                     (out_imagefile,out_maskfile,src,width,height,time))

      if not job['no_annotations']:
        extract_annotations (work_dir, c_out, cad, camera, out_imagefile, monitor)
        conn_out.commit()

      print 'wrote frame %d' % i_out
      i_out += 1

      if not job['save_blender_files']: 
        shutil.rmtree(work_dir)

  conn_out.commit()
  conn_in.close()
  conn_out.close()

  pool.close()
  pool.join()


def create_in_db (job):
  ''' Create in_db_file from video, unless it already exists '''
  # figure out where is the actual video
  assertParamIsThere  (job, 'video_dir')
  assertParamIsThere  (job, 'out_video_dir')
  video_dir = job['video_dir']
  camera_name = op.basename(op.dirname(video_dir))
  video_name  = op.basename(video_dir)
  camdata_video_dir = op.join('camdata', camera_name, video_name)
  # figure out where will be the init db
  db_prefix = op.join(job['out_video_dir'], 'init')
  # update the job
  in_db_file = '%s-back.db' % db_prefix

  if not op.exists(atcity(in_db_file)):
    logging.info ('will create in_db_file from video: %s' % in_db_file)
    make_dataset (camdata_video_dir, db_prefix, params={'videotypes': ['back']})
  else:
    logging.warning ('in_db_file exists. Will not rewrite it: %s' % in_db_file)

  return in_db_file