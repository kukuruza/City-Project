#!/usr/bin/env python
import os, os.path as op
from lib.scene import Camera, Pose
import logging
import argparse
import cv2
import numpy as np
import math
from imageio import imwrite, get_writer
from lib.scene import Pose
from lib.labelMatches import loadMatches
from lib.warp import warpPoseToMap

if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('--camera_id', required=True, type=int)
  parser.add_argument('--map_id', type=int, help='If not set, will use pose["best_map_id"]')
  parser.add_argument('--pose_id', type=int, default=0)
  parser.add_argument('--update_map_json', action='store_true')
  parser.add_argument('--no_backup', action='store_true')
  parser.add_argument('--ransac', action='store_true')
  parser.add_argument('--logging', type=int, default=20, choices=[10,20,30,40])
  args = parser.parse_args()
  
  logging.basicConfig(level=args.logging, format='%(levelname)s: %(message)s')

  pose = Pose(args.camera_id, pose_id=args.pose_id, map_id=args.map_id)

  # Load matches.
  in_matches_path1 = op.join(pose.get_pose_dir(), 'matches-map%d.json' % pose.map_id)
  in_matches_path2 = op.join(pose.get_pose_dir(), 'matches.json')
  if op.exists(in_matches_path1):
    src_pts, dst_pts = loadMatches(in_matches_path1, 'frame', 'map')
  elif op.exists(in_matches_path2):
    src_pts, dst_pts = loadMatches(in_matches_path2, 'frame', 'map')
  else:
    raise Exception('No file %s or %s' % (in_matches_path1, in_matches_path2))

  # Compute video->pose homography.
  src_pts = src_pts.reshape(-1,1,2)
  dst_pts = dst_pts.reshape(-1,1,2)
  method = cv2.RANSAC if args.ransac else 0
  H, _ = cv2.findHomography(src_pts, dst_pts, method=method)
  pose['maps'][pose.map_id]['H_frame_to_map'] = H.copy().reshape((-1,)).tolist()
  print H

  # Compute the origin on the map.
  satellite = pose.map.load_satellite()
  X1 = H[:,1].copy().reshape(-1)
  X1 /= X1[2]
  logging.debug('Vertically down line projected onto map: %s' % str(X1))
  frameH = pose.camera['cam_dims']['height']
  frameW = pose.camera['cam_dims']['width']
  X2 = np.dot(H, np.asarray([[frameW/2],[frameH/2],[1.]], dtype=float)).reshape(-1)
  X2 /= X2[2]
  logging.debug('Frame center projected onto map: %s' % str(X2))
  cv2.circle(satellite, (int(X2[0]),int(X2[1])), 6, (0,255,0), 4)
  if 'cam_origin' in pose.camera and 'z' in pose.camera['cam_origin']:
    # TODO: find out how to infer height, focal length, and FOV from homography.
    h = pose.camera['cam_origin']['z']
  else:
    logging.warning('No camera height, will use 8.5 m')
    h = 8.5
  h *= pose.map['pxls_in_meter']
  l = math.sqrt((X1[0]-X2[0])*(X1[0]-X2[0])+(X1[1]-X2[1])*(X1[1]-X2[1]))
  d = math.sqrt(1 - 4*h*h/l/l)
  logging.info ('Discriminant for origin computation: %.2f' % d)
  # Assume the camera is not looking that much down.
  X0 = (1. + d) / 2 * X1 + (1. - d) / 2 * X2
  logging.info('Camera origin (x,y) on the map: (%d,%d)' % (X0[0], X0[1]))
  cv2.circle(satellite, (int(X0[0]),int(X0[1])), 6, (0,255,0), 4)
  pose['maps'][pose.map_id]['map_origin'] = {
      'x': int(X0[0]), 'y': int(X0[1]), 'comment': 'computed by ComputeH.py'}

  # Save.
  if args.update_map_json:
    # Propagate this infomation forward on to map.json.
    pose.map['map_origin'] = {
       'x': int(X0[0]), 'y': int(X0[1]), 
       'comment': 'computed by ComputeH from pose %d' % pose.pose_id
    }
  pose.save(backup=not args.no_backup)

  # Warp satellite for nice visualization.
  warped_satellite = warpPoseToMap(satellite, args.camera_id, pose.pose_id, pose.map_id,
                                   reverse_direction=True)
  warped_path = op.join(pose.get_pose_dir(), 'satellite-warped-map%d.gif' % pose.map_id)
  poseframe = pose.load_example()
  with get_writer(warped_path, mode='I') as writer:
    for i in range(10):
      writer.append_data((poseframe / 10. * i +
                          warped_satellite / 10. * (10. - i)).astype(np.uint8))

  # Make visibility map.
  # Horizon line.
  horizon = H[2,:].copy().transpose()
  logging.debug('Horizon line: %s' % str(horizon))
  assert horizon[1] != 0
  x1 = 0
  x2 = frameW-1
  y1 = int(- (horizon[0] * x1 + horizon[2]) / horizon[1])
  y2 = int(- (horizon[0] * x2 + horizon[2]) / horizon[1])
  # Visible part in the frame.
  visibleframe = np.ones((frameH, frameW), np.uint8) * 255
  cv2.fillPoly(visibleframe, np.asarray([[(x1,y1),(x2,y2),(x2,0),(x1,0)]]), (0,))
  # Visible part in the satallite.
  visiblemap = warpPoseToMap(visibleframe, args.camera_id, pose.pose_id, pose.map_id)
  # Would be nice to store visiblemap as alpha channel, but png takes too much space.
  alpha_mult = np.tile(visiblemap.astype(float)[:,:,np.newaxis] / 512 + 0.5, 3)
  visiblemap = (satellite * alpha_mult).astype(np.uint8)
  visibility_path = op.join(pose.get_pose_dir(), 'visible-map%d.jpg' % pose.map_id)
  imwrite(visibility_path, visiblemap)
