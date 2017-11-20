#!/usr/bin/env python
import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
from scenes.lib.camera import Camera, Pose
import simplejson as json
import logging
import shutil
import argparse
import cv2
import numpy as np
from random import choice
from pprint import pprint
from scipy.misc import imread, imsave


if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  #parser.add_argument('--in_matches_path', required=True)
  parser.add_argument('--camera', required=True, default="cam572")
  parser.add_argument('--pose_id', type=int, default=0)
  parser.add_argument('--logging', type=int, default=20, choices=[10,20,30,40])
  args = parser.parse_args()
  
  logging.basicConfig(level=args.logging, format='%(levelname)s: %(message)s')

  in_matches_path = op.join(
    'data/scenes', args.camera, 'pose%d' % args.pose_id, 'matches.json')
  assert op.exists(in_matches_path), in_matches_path
  matches = json.load(open(in_matches_path))
  pprint (matches)
  src_pts = matches['frame']
  dst_pts = matches['map']

  assert range(len(src_pts['x'])) == range(len(dst_pts['x']))
  assert range(len(src_pts['x'])) == range(len(src_pts['y']))
  assert range(len(dst_pts['x'])) == range(len(dst_pts['y']))
  N = range(len(src_pts['x']))

  src_pts = np.float32([ [src_pts['x'][i], src_pts['y'][i]] for i in N ])
  dst_pts = np.float32([ [dst_pts['x'][i], dst_pts['y'][i]] for i in N ])
  print (src_pts)
  print (dst_pts)

  src_pts = src_pts.reshape(-1,1,2)
  dst_pts = dst_pts.reshape(-1,1,2)
  H, _ = cv2.findHomography(src_pts, dst_pts, 0)
  print H

  camera = Camera(args.camera)
  camera['poses'][args.pose_id]['H_frame_to_map'] = H.reshape((-1,)).tolist()
  camera.save()

  pose = Pose(args.camera, pose_id=args.pose_id)
  
  satellite = pose.load_satellite()
  frame = pose.load_frame()
  size = (frame.shape[1], frame.shape[0])
  warped_satellite = cv2.warpPerspective(satellite, np.linalg.inv(H), size)
  warped_path = op.join(pose.get_pose_dir(), 'warped_satellite.jpg')
  imsave(warped_path, warped_satellite)

  print (camera.dump())
