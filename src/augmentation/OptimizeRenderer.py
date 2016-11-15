import sys, os, os.path as op
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import numpy as np
import cv2
import argparse
import logging
import json
from pprint import pprint
import multiprocessing

from learning.helperSetup import dbInit, setupLogging, atcity
from learning.helperImg   import ReaderVideo
from learning.helperDb    import carField
from learning.dbUtilities import bbox2roi
from Video import Video
from processScene import mywrapper, render_frame, combine_frame
from placeCars import axes_png2blender


WORK_RENDER_DIR     = atcity('augmentation/blender/current-frame')
RENDERED_FILENAME   = 'render.png'
CARSONLY_FILENAME   = 'cars-only.png'


def _crop(frame, bbox):
  roi = bbox2roi(bbox)
  logging.debug('_crop, roi: %s' % str(roi))
  crop = frame[roi[0]:roi[2]+1, roi[1]:roi[3]+1, :]
  return crop


def get_cost_for_frame (frame_ref, frame_gen, bbox):
  crop_ref = _crop(frame_ref, bbox).astype(float).flatten()
  crop_gen = _crop(frame_gen, bbox).astype(float).flatten()
  loss = np.linalg.norm(crop_ref - crop_gen, ord=1)
  loss = loss / crop_ref.size
  return loss


def _get_warped_coords (x, y, H):
  '''Get coordinates of a point warped by a homography'''
  logging.debug('before _get_warped_coords: %0.2f, %0.2f' % (x, y))
  p = np.array([x, y, 1])
  p = np.dot(H, p)
  x, y = p[0]/p[2], p[1]/p[2]
  logging.debug('after  _get_warped_coords: %0.2f, %0.2f' % (x, y))
  return int(x), int(y)



def _init_traffic_gen (camera, video, bbox, H):
  # get the map of azimuths. 
  # it has gray values (r==g==b=) and alpha, saved as 4-channels
  camera.info['azimuth_name'] = 'google1/azimuth2-filled.png'
  azimuth_path = atcity(op.join(camera.info['camera_dir'], camera.info['azimuth_name']))
  azimuth_map = cv2.imread (azimuth_path, cv2.IMREAD_UNCHANGED)
  assert azimuth_map is not None and azimuth_map.shape[2] == 4
  azimuth_map = azimuth_map[:,:,0]

  # estimate x0,y0,size0,azimuth0,model
  # approximate car centers in the original image [x,y,1]
  x0, y0 = bbox[0]+bbox[2]/2, bbox[1]+bbox[3]*0.75
  x0, y0 = _get_warped_coords (x0, y0, H)
  logging.info('azimuth at (y0,x0): %d' % azimuth_map[y0][x0])

  azimuth = azimuth_map[y0][x0] * 2
  #scale0 = 1
  collection_id = "7c7c2b02ad5108fe5f9082491d52810"
  model_id      = "40f160e49a6d0b3b3e483abd80a2f41"
  vehicles_gen  = [{'x': x0, 'y': y0, 'azimuth': azimuth,
                    'collection_id': collection_id, 'model_id': model_id}]
  axes_png2blender (vehicles_gen, camera.info['origin_image'], camera.info['pxls_in_meter'])
  traffic_gen   = {'vehicles': vehicles_gen, 'weather': video.info['weather'],
                   'sun_altitude': 0, 'sun_azimuth': 0}
  return traffic_gen



def mycombinewrapper((video, camera, back, params)):
  ''' wrapper for parallel processing. Argument is an element of frame_jobs 
  '''
  WORK_DIR = '%s-%d' % (WORK_RENDER_DIR, os.getpid())
  PARENT_DIR = '%s-%d' % (WORK_RENDER_DIR, os.getppid())

  rendered = cv2.imread(op.join(PARENT_DIR, RENDERED_FILENAME), -1)
  carsonly = cv2.imread(op.join(PARENT_DIR, CARSONLY_FILENAME), -1)

  rendered = np.roll(rendered, params['dy'], 0)
  rendered = np.roll(rendered, params['dx'], 1)
  carsonly = np.roll(carsonly, params['dy'], 0)
  carsonly = np.roll(carsonly, params['dx'], 1)

  if not op.exists(WORK_DIR):
    os.makedirs(WORK_DIR)
  cv2.imwrite(op.join(WORK_DIR, RENDERED_FILENAME), rendered)
  cv2.imwrite(op.join(WORK_DIR, CARSONLY_FILENAME), carsonly)

  out_image = combine_frame (back, video, camera)

  return out_image, params




def optimization (camera, video, c_ref, back, params):

#  WORK_DIR = '%s-%d' % (WORK_RENDER_DIR, os.getpid())

  c_ref.execute('SELECT * FROM cars')
  car_entries = c_ref.fetchall()

  image_reader = ReaderVideo()

  # temp: take the first car entry
  imagefile = carField(car_entries[0], 'imagefile')
  logging.info ('imagefile: %s' % imagefile)
  frame_ref = image_reader.imread(imagefile)
  cv2.imwrite('/Users/evg/Desktop/frame.png', frame_ref)
  bbox = carField(car_entries[0], 'bbox')

  H = np.array([
    [-2.0656e-01,  -3.5475e+00,   4.4801e+02],
    [-2.5851e-02,  -6.8153e+00,   8.3446e+02],
    [-6.1211e-05,  -9.6092e-03,   1.]
  ])
    # [-1.9643e-01,  -3.6140e+00,   4.5061e+02],
    # [-1.5423e-02,  -6.9939e+00,   8.5201e+02],
    # [-2.0333e-05,  -9.7870e-03,   1.]

  jobs = []

  traffic = _init_traffic_gen (camera, video, bbox, H)
  traffic['save_blender_files'] = params['save_blender_files']
  _, _ = render_frame(video, camera, traffic)

  ixs = range(-7,8)
  iys = range(-7,8)
  step = 0.1

  losses = np.zeros((len(iys),len(ixs)), dtype=float)
  crops  = np.zeros((len(iys)*bbox[3], len(ixs)*bbox[2], 3), dtype=np.uint8)
  for idx,ix in enumerate(ixs):
    for idy,iy in enumerate(iys):
      dx = int(ix * step * bbox[2])
      dy = int(iy * step * bbox[3])
      job = (video, camera, back, 
        {'idx':idx, 'idy':idy, 'dx':dx, 'dy':dy, 'ix':ix, 'iy':iy})
      jobs.append(job)

  pool = multiprocessing.Pool()
  for frame_gen, params in pool.imap(mycombinewrapper, jobs):
    loss = get_cost_for_frame (frame_ref, frame_gen, bbox)
    crop_gen = _crop(frame_gen, bbox)
    losses[params['iy']][params['ix']] = loss
    crops [params['idy']*bbox[3] : (params['idy']+1)*bbox[3], 
           params['idx']*bbox[2] : (params['idx']+1)*bbox[2], :] = crop_gen.copy()

  print losses
  cv2.imshow('crops', crops)
  cv2.waitKey(-1)

  


if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('--logging_level', default=20, type=int)
  parser.add_argument('--ref_db_file', required=True, help='db with real cars')
  parser.add_argument('--back_file', required=True, help='background file')
  parser.add_argument('--video_dir', required=True)
  parser.add_argument('--save_blender_files', action='store_true')
  args = parser.parse_args()

  setupLogging ('log/augmentation/OptimizeRenderer.log', args.logging_level, 'w')

  video = Video(video_dir=args.video_dir)
  camera = video.build_camera()

  params = {}
  params['save_blender_files'] = args.save_blender_files

  back = cv2.imread(atcity(args.back_file))
  assert back is not None

  (conn, cursor) = dbInit(args.ref_db_file)
  optimization(camera, video, cursor, back, params)
  conn.close()
