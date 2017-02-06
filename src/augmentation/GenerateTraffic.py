#!/usr/bin/env python
import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import argparse
import json, simplejson
import logging
from pprint import pprint 
from learning.helperSetup import setupLogging, atcity
from learning.helperSetup import assertParamIsThere, setParamUnlessThere
from learning.video2dataset import make_dataset
from Cad import Cad
from Camera import Camera
from Video import Video
from traffic import TrafficModel, TrafficModelRandom
import sqlite3
from processScene import Diapason, get_time



def generate_video_traffic (job):
  ''' Generate traffic file for the whole video.
  Args:
    in_db_file - should have all the images for which traffic is generated
    job - the same as for process_video
  '''
  assertParamIsThere  (job, 'in_db_file')
  assertParamIsThere  (job, 'out_video_dir')
  setParamUnlessThere (job, 'frame_range', '[::]')
  assertParamIsThere  (job, 'video_dir')
  assertParamIsThere  (job, 'speed_kph')  # TODO random or this

  video = Video(video_dir=job['video_dir'])
  camera = video.build_camera()

  assert op.exists(atcity(job['in_db_file'])), \
      'in db %s does not exist' % atcity(job['in_db_file'])
  conn_in = sqlite3.connect(atcity(job['in_db_file']))
  c_in = conn_in.cursor()
  c_in.execute('SELECT time FROM images')
  timestamps = c_in.fetchall()
  conn_in.close()

  cad = Cad(job['collection_names'])

  traffic_model = TrafficModel (camera, video, cad=cad, speed_kph=job['speed_kph'])
  #traffic_model = TrafficModelRandom (camera, video, cad=cad, num_cars=job['num_cars'])

  diapason = Diapason (len(timestamps), job['frame_range'])
  
  traffic = {'in_db_file': job['in_db_file']}
  traffic['frames'] = []

  for frame_id in diapason.frame_range:
    logging.info ('generating traffic for frame %d' % frame_id)
    timestamp = timestamps[frame_id][0]
    time = get_time (video, timestamp, frame_id)
    traffic_frame = traffic_model.get_next_frame(time)
    traffic_frame['frame_id'] = frame_id  # for validating
    traffic['frames'].append(traffic_frame)

  return traffic


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--logging_level', default=20, type=int)
    parser.add_argument('--speed_kph', type=int, required=True)
    parser.add_argument('--frame_range', default='[::]', 
                        help='python style ranges, e.g. "[5::2]"')
    parser.add_argument('--job_file', required=True)
    parser.add_argument('--in_db_file', required=True)
    parser.add_argument('--traffic_file', required=True,
                        help='output .json file where to write traffic info. '
                             'Can be "traffic.json" in video output dir.')
    args = parser.parse_args()

    setupLogging('log/augmentation/GenerateTraffic.log', args.logging_level, 'w')

    if not op.exists(atcity(op.dirname(args.traffic_file))):
      os.makedirs(atcity(op.dirname(args.traffic_file)))
              
    assert op.exists(atcity(args.job_file)), atcity(args.job_file)
    job = simplejson.load(open(atcity(args.job_file) ))
    setParamUnlessThere (job, 'speed_kph', args.speed_kph)
    setParamUnlessThere (job, 'frame_range', args.frame_range)
    setParamUnlessThere (job, 'in_db_file', args.in_db_file)
    setParamUnlessThere (job, 'video_dir', op.dirname(args.job_file))
    setParamUnlessThere (job, 'out_video_dir', op.dirname(args.in_db_file))
    
    pprint (job)
    traffic = generate_video_traffic (job)
    with open(atcity(args.traffic_file), 'w') as f:
      f.write(json.dumps(traffic, indent=2))

