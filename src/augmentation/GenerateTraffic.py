#!/usr/bin/env python
import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import argparse
import json
import logging
from learning.helperSetup import setupLogging, atcity
from learning.helperSetup import assertParamIsThere, setParamUnlessThere
from learning.video2dataset import make_dataset
from Cad import Cad
from Camera import Camera
from Video import Video
from traffic import TrafficModel
import sqlite3
from processScene import Diapason, get_time



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
  frame_range_str = job['frame_range'].replace(':','-').replace(':','-')
  in_db_prefix = op.join(job['out_video_dir'], 'init-%s' % frame_range_str)
  in_db_file = '%s-back.db' % in_db_prefix

  if not op.exists(atcity(in_db_file)):
    logging.info ('will create in_db_file from video: %s' % in_db_file)
    make_dataset (camdata_video_dir, in_db_prefix, params={'videotypes': ['back']})
  else:
    logging.warning ('in_db_file exists. Will not rewrite it: %s' % in_db_file)

  return in_db_file


def generate_video_traffic (job):
  ''' Generate traffic file for the whole video.
  Args:
    job - the same as for process_video
  '''
  assertParamIsThere  (job, 'out_video_dir')
  setParamUnlessThere (job, 'frame_range', '[::]')
  assertParamIsThere  (job, 'video_dir')

  video = Video(video_dir=job['video_dir'])
  camera = video.build_camera()

  in_db_file = create_in_db(job)   # creates in_db_file if necessary
  assert op.exists(atcity(in_db_file)), 'in db %s does not exist' % atcity(in_db_file)
  conn_in = sqlite3.connect(atcity(in_db_file))
  c_in = conn_in.cursor()
  c_in.execute('SELECT time FROM images')
  timestamps = c_in.fetchall()
  conn_in.close()

  cad = Cad()
  cad.load(job['collection_names'])

  traffic_model = TrafficModel (camera, video, cad=cad, speed_kph=job['speed_kph'])

  diapason = Diapason (len(timestamps), job['frame_range']).intersect(
             Diapason (len(timestamps), video.info['frame_range']) )
  
  traffic = {'in_db_file': in_db_file}
  traffic['frames'] = []

  for frame_id in diapason.frame_range:
    logging.info ('generating traffic for frame %d' % frame_id)
    timestamp = timestamps[frame_id][0]
    time = get_time (video, timestamp, frame_id)
    traffic_frame = traffic_model.get_next_frame(time)
    traffic_frame['frame_id'] = frame_id  # for validating
    traffic['frames'].append(traffic_frame)

  return traffic



def add_args_to_job(job, args):
    if 'frame_range' not in job:
        job['frame_range'] = args.frame_range


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--logging_level', default=20, type=int)
    parser.add_argument('--frame_range', default='[::]', 
                        help='python style ranges, e.g. "[5::2]"')
    parser.add_argument('--job_file', required=True)
    parser.add_argument('--traffic_file', required=True,
                        help='output .json file where to write traffic info. '
                             'Can be "traffic.json" in video output dir.')
    args = parser.parse_args()

    setupLogging('log/augmentation/GenerateTraffic.log', args.logging_level, 'w')

    if not op.exists(atcity(op.dirname(args.traffic_file))):
      os.makedirs(atcity(op.dirname(args.traffic_file)))
              
    job = json.load(open(atcity(args.job_file) ))
    add_args_to_job(job, args)
    
    traffic = generate_video_traffic (job)

    with open(atcity(args.traffic_file), 'w') as f:
      f.write(json.dumps(traffic, indent=4))

