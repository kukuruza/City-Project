#!/usr/bin/env python3
import os, os.path as op
from lib.scene import Camera, Pose
import logging
import argparse
import cv2
import numpy as np
import math
from glob import glob
from lib.scene import Pose, Map, _atcity
from lib.warp import warp

"""
Make a big NYC satellite snapshot with camera visibility maps.
"""

def makeLinearCircularKernel(radius):
  image = np.zeros((2*radius+1,2*radius+1), dtype=float)
  image = cv2.circle(image, (radius+1,radius+1), radius//2, (255,), -1)
  image = cv2.filter2D(image, ddepth=cv2.CV_32F, kernel=image, borderType=cv2.BORDER_CONSTANT)
  image /= image.max()
  image_disp = (image * 255).astype(np.uint8)
  return image


def getCameraCircleMask(shape, x, y, radius):
  # Make a image with a single white point.
  assert len(shape) == 2
  image = np.zeros(shape, dtype=float)
  image[y,x] = 1.
  # Make a kernel for that shape.
  kernel = makeLinearCircularKernel(radius)
  # Convolve the single white point with kernel and scale back to 1 max.
  image = cv2.filter2D(image, ddepth=cv2.CV_32F, kernel=kernel, borderType=cv2.BORDER_CONSTANT)
  image /= image.max()
  return image
  


def apply_H(H, x, y):
  dst = np.dot(H, np.asarray([[x],[y],[1.]])).reshape(-1)
  dst /= dst[2]
  return dst


def H_from_points(pxls_to_coords, name):
  ''' Return H from pxl<->coords correspondences. '''

  logging.info('Called for camera %s' % name)
  p1 = pxls_to_coords[0]
  p2 = pxls_to_coords[1]
  avg_lat_rad = ((p2['lat'] + p1['lat']) / 2) * (np.pi / 180)
  sx = float(p2['lon'] - p1['lon']) / float(p2['x'] - p1['x'])
  sy = float(p2['lat'] - p1['lat']) / float(p2['y'] - p1['y'])
  bx = p1['lon'] - sx * p1['x']
  by = p1['lat'] - sy * p1['y']
  logging.debug('sx=%f, sy=%f, bx=%f, by=%f' % (sx*1000, sy*1000, bx, by))
  H = np.array([[sx,0,bx],[0,sy,by],[0,0,1]], dtype=np.float64)
  logging.info('Computed H (pixels to degrees):\n%s' % str(H))

  # Find coordinates of the two GT points to check correctness
  p1_coord = apply_H (H, p1['x'], p1['y'])
  p2_coord = apply_H (H, p2['x'], p2['y'])
  logging.debug('point1 coord: gt=[%f, %f], computed=[%f, %f]' %
    (p1['lon'], p1['lat'], p1_coord[0], p1_coord[1]))
  logging.debug('point2 coord: gt=[%f, %f], computed=[%f, %f]' %
    (p2['lon'], p2['lat'], p2_coord[0], p2_coord[1]))

  return H


def wrapVisibilityFrameToMap(H, src_shape, dst_shape, height):
  ''' Wrap the visible part of the frame into map. '''

  frameH, frameW = src_shape[0], src_shape[1]
  mapH, mapW = dst_shape[0], dst_shape[1]
  visibleframe = np.ones((frameH, frameW), np.uint8) * 255

  # Horizon line.
  horizon = H[2,:].copy().transpose()
  logging.debug('Horizon line: %s' % str(horizon))
  assert horizon[1] != 0
  x1 = 0
  x2 = frameW-1
  y1 = int(- (horizon[0] * x1 + horizon[2]) / horizon[1])
  y2 = int(- (horizon[0] * x2 + horizon[2]) / horizon[1])

  # Visible part in the frame.
  cv2.fillPoly(visibleframe, np.asarray([[(x1,y1),(x2,y2),(x2,0),(x1,0)]]), (0,))

  # Visible part in the bigpic.
  visiblemap = warp(visibleframe, H, (frameH, frameW), (mapH, mapW))
  return visiblemap


def computeCameraRange(H, frameW, frameH):

  # Compute the origin on the map.
#  satellite = pose.map.load_satellite()
  X1 = H[:,1].copy().reshape(-1)
  X1 /= X1[2]
  logging.debug('Vertically down line projected onto map: %s' % str(X1))
  X2 = apply_H (H, frameW/2, frameH/2)
  logging.debug('Frame center projected onto map: %s' % str(X2))
  #cv2.circle(satellite, (int(X2[0]),int(X2[1])), 6, (0,255,0), 4)
  #h *= pose.map['pxls_in_meter']
  l = math.sqrt((X1[0]-X2[0])*(X1[0]-X2[0])+(X1[1]-X2[1])*(X1[1]-X2[1]))
  logging.info('Camera radius is estimated to be %.1f pixels.' % l)
  #d = math.sqrt(1 - 4*h*h/l/l)
  #logging.info ('Discriminant for origin computation: %.2f' % d)
  # Assume the camera is not looking that much down.
  #X0 = (1. + d) / 2 * X1 + (1. - d) / 2 * X2
  #logging.info('Camera origin (x,y) on the map: (%d,%d)' % (X0[0], X0[1]))
  #cv2.circle(satellite, (int(X0[0]),int(X0[1])), 6, (0,255,0), 4)
  return l


def getVisibleMapForCamera(camera_id, bigpic_shape, H_bigpic_to_coord, default_height):
  ''' Project a visibility map onto the global map for pose=0 of camera_id. '''

  pose = Pose(camera_id, pose_id=0)

  frameH = pose.camera['cam_dims']['height']
  frameW = pose.camera['cam_dims']['width']
  bigpicH = bigpic_shape[0]
  bigpicW = bigpic_shape[1]

  # H from frame to map.
  H_frame_to_map = np.asarray(pose['H_pose_to_map']).reshape((3,3))
  logging.debug('H_pose_to_map:\n%s' % str(H_frame_to_map))

  # H from map to coordinates.
  points = pose.map['pxls_to_coords']
  H_map_to_coords = H_from_points(points, name=str(camera_id))
  logging.debug('H_map_to_coords:\n%s' % str(H_map_to_coords))

  # H from frame to bigpic.
  H_frame_to_bigpic = np.dot(np.linalg.solve(H_bigpic_to_coord, H_map_to_coords), H_frame_to_map)
  logging.info('H_frame_to_bigpic:\n%s' % str(H_frame_to_bigpic))

  # Make visibility map.
  visible_bigpic = wrapVisibilityFrameToMap(H_frame_to_bigpic, (frameH, frameW), (bigpicH, bigpicW), height=default_height)

  # H from map to bigpic to draw the origin.
  H_map_to_bigpic = np.linalg.solve(H_bigpic_to_coord, H_map_to_coords)
  origin_map = pose.map['map_origin']
  origin_bigpic = apply_H (H_map_to_bigpic, origin_map['x'], origin_map['y'])
  logging.info('Origin of camera %s projected to bigmap at: x=%d,y=%d' %
      (str(camera_id), origin_bigpic[0], origin_bigpic[1]))
  cv2.circle(visible_bigpic, (int(origin_bigpic[0]), int(origin_bigpic[1])), 3, (255,), -1)

  # Each camera has a average radius. Compute it and filter the mask.
  radius_of_frame_center = computeCameraRange(H_frame_to_bigpic, frameH, frameW)
  RADIUS_MULT = 20
  radius_mask = getCameraCircleMask(
      shape=(bigpicH,bigpicW), x=int(origin_bigpic[0]), y=int(origin_bigpic[1]),
      radius=int(radius_of_frame_center * RADIUS_MULT))
  visible_bigpic = (visible_bigpic.astype(float) * radius_mask).astype(np.uint8)

  return visible_bigpic


if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('--bigpic_mapid', type=int, default=0,
    help='just like for cameras, bigpic has maps.')
  parser.add_argument('--camera_ids', nargs='*', type=int, required=False,
    help='if given use only one camera, if not given use all cameras.')
  parser.add_argument('--default_height', type=float, default=8.5)
  parser.add_argument('--logging', type=int, default=20, choices=[10,20,30,40])
  args = parser.parse_args()
  
  #FORMAT = '[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s'
  logging.basicConfig(level=args.logging, format='%(funcName)s.%(lineno)s: %(message)s')

  # Load bigpic and its information.
  bigpicmap = Map(camera_id='bigpic', map_id=args.bigpic_mapid)
  points = bigpicmap['pxls_to_coords']
  H_bigpic_to_coord = H_from_points(points, name='bigpic')
  bigpic = cv2.imread(_atcity('data/scenes/bigpic/map%d/map.png' % args.bigpic_mapid))

  if args.camera_ids is not None:
    camera_ids = args.camera_ids
  else:
    camera_ids = glob(_atcity('data/scenes/???'))
  logging.info('Will use cameras: %s' % str(camera_ids))

  visiblemap = np.zeros(shape=bigpic.shape[:2], dtype=np.uint8)
  for camera_id in camera_ids:

    visiblemap_cam = getVisibleMapForCamera(
        camera_id, bigpic.shape, H_bigpic_to_coord, args.default_height)
    visiblemap += visiblemap_cam

  alpha_mult = np.tile(visiblemap.astype(float)[:,:,np.newaxis] / 512 + 0.5, 3)
  visiblemap = (bigpic * alpha_mult).astype(np.uint8)
  visibility_path = _atcity('data/scenes/bigpic/map%d/visibility.jpg' % args.bigpic_mapid)
  cv2.imwrite(visibility_path, visiblemap)

