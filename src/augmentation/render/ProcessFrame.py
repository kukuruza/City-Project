#!/usr/bin/env python
import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import argparse
import simplejson as json
import cv2
from processScene import render_frame, combine_frame
from Video import Video
from Camera import Camera
from Cad import Cad
from learning.helperSetup import setupLogging, atcity


if __name__ == "__main__":
  '''Render a frame using default video's background.
     Leave the frame at the default blender location'''

  parser = argparse.ArgumentParser()
  parser.add_argument('--work_dir', required=True)
  parser.add_argument('--video_dir', required=True)
  parser.add_argument('--save_blender_files', action='store_true')
  parser.add_argument('--no_combine', action='store_true')
  parser.add_argument('--no_render', action='store_true')
  parser.add_argument('--no_annotations', action='store_true')
  parser.add_argument('--logging_level', default=20, type=int)
  parser.add_argument('--background_file',
                      help='if not given, take the default from video_dir')
  args = parser.parse_args()

  setupLogging('log/augmentation/ProcessFrame.log', args.logging_level, 'w')

  traffic = json.load(open(atcity(op.join(args.work_dir, 'traffic.json'))))
  traffic['save_blender_files'] = args.save_blender_files
  traffic['render_individual_cars'] = not args.no_annotations

  video = Video(video_dir=args.video_dir)
  camera = video.build_camera()

  if not args.no_render:
    render_frame (video, camera, traffic, work_dir=args.work_dir)
  if not args.no_combine:
    back_file = op.join(args.work_dir, 'background.png')
    background = cv2.imread(atcity(back_file))
    combine_frame (background, video, camera, work_dir=args.work_dir)
