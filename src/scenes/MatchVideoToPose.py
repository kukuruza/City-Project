#!/usr/bin/env python
import os, os.path as op
import logging
import argparse
import cv2
from pkg_resources import parse_version
from lib.labelMatches import labelMatches
from lib.scene import Pose, _atcity


# returns OpenCV VideoCapture property id given, e.g., "FPS"
def _capPropId(prop):
  OPCV3 = parse_version(cv2.__version__) >= parse_version('3')
  return getattr(cv2 if OPCV3 else cv2.cv, ("" if OPCV3 else "CV_") + "CAP_PROP_" + prop)


if __name__ == "__main__":

  parser = argparse.ArgumentParser(description=
      '''Match a frame from a video to the closest pose''')
  parser.add_argument('--video_file', required=True, type=str)
  parser.add_argument('--camera_id', required=True, type=int)
  parser.add_argument('--pose_id', type=int, 
      help='If left blank, take the value from videos.json')
  parser.add_argument('--video_frame_id', type=int, default=0,
      help='Sometimes the first video frame is not best for fitting.')
  parser.add_argument('--no_backup', action='store_true')
  parser.add_argument('--winsize1', type=int, default=700)
  parser.add_argument('--winsize2', type=int, default=700)
  parser.add_argument('--logging', type=int, default=20, choices=[10,20,30,40])
  args = parser.parse_args()
  
  logging.basicConfig(level=args.logging, format='%(levelname)s: %(message)s')

  # Find pose_id in video.json file if not provided.
  if args.pose_id is None:
    assert 0  # FIXME: implement
  else:
    pose_id = args.pose_id

  # Load pose and its example frame.
  pose = Pose(camera_id=args.camera_id, pose_id=pose_id)
  poseframe = pose.load_frame()

  # Load a frame from a video.
  video_path = _atcity(args.video_file)
  assert op.exists(video_path), video_path
  video = cv2.VideoCapture(_atcity(args.video_file))
  assert video, 'Video failed to open: %s' % video
  video_length = int(video.get(_capPropId('FRAME_COUNT')))
  assert args.video_frame_id < video_length
  video.set(_capPropId('POS_FRAMES'), args.video_frame_id)
  retval, videoframe = video.read()
  if not retval:
    raise Exception('Failed to read the frame.')

  video_name = op.splitext(op.basename(args.video_file))[0]
  matches_dir = op.join(pose.camera.get_camera_dir(), 'matches')
  if not op.exists(matches_dir):
    os.makedirs(matches_dir)
  matches_path = op.join(matches_dir, '%s-pose%d.json' % (video_name, pose_id))

  labelMatches (videoframe, poseframe, matches_path,
      winsize1=args.winsize1, winsize2=args.winsize2,
      name1='video', name2='pose',
      backup_matches=not args.no_backup)
