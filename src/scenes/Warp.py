#!/usr/bin/env python
import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
from scenes.lib.camera import Pose
from scenes.lib.maskedDilation import maskedDilation
import simplejson as json
import logging
import argparse
import cv2
import numpy as np
from pprint import pprint


def warp(in_image, camera_id, pose_id, map_id,
    dilation_radius=None, reverse_direction=False):  

  pose = Pose(camera_id, pose_id=pose_id, map_id=map_id)
  H = np.asarray(pose['maps'][pose.map_id]['H_frame_to_map']).reshape((3,3))
  dims_in = (pose.camera['cam_dims']['height'], pose.camera['cam_dims']['width'])
  dims_out = (pose.map['map_dims']['height'], pose.map['map_dims']['width'])
  np.set_printoptions(precision=1,
      formatter = dict( float = lambda x: "%10.4f" % x ))
  logging.debug (str(H))
  logging.debug ('dims_in: %s' % str(dims_in))
  logging.debug ('dims_out: %s' % str(dims_out))
  if reverse_direction:
    H = np.linalg.inv(H)
    dims_in, dims_out = dims_out, dims_in

  assert in_image is not None
  logging.debug('Type of input image: %s' % str(in_image.dtype))

  if dilation_radius is not None and dilation_radius > 0:
    kernelsize = dilation_radius * 2 + 1
    kernel = np.ones((kernelsize, kernelsize), dtype=float)
    in_image = maskedDilation(in_image, kernel)

  # If input is on the wrong scale, need to use another homography first.
  in_scale_h = float(dims_in[0]) / in_image.shape[0]
  in_scale_w = float(dims_in[1]) / in_image.shape[1]
  assert (in_scale_w - in_scale_h) / (in_scale_w + in_scale_h) < 0.01
  H_scale = np.identity(3, dtype=float)
  H_scale[0,0] = in_scale_h
  H_scale[1,1] = in_scale_w
  H_scale[2,2] = 1.
  H = np.matmul(H, H_scale)
  logging.info('Scaling input image with (%f %f)' % (in_scale_h, in_scale_w))
  logging.debug (str(H))

  out_image = cv2.warpPerspective(in_image, H, (dims_out[1], dims_out[0]), flags=cv2.INTER_NEAREST)
  logging.debug('Type of output image: %s' % str(out_image.dtype))

  return out_image


if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('--camera', required=True, help="E.g., '572'.")
  parser.add_argument('--in_image_path', required=True)
  parser.add_argument('--out_image_path')
  parser.add_argument('--pose_id', type=int, default=0)
  parser.add_argument('--dilation_radius', help='Optional dilation on input image.', type=int)
  parser.add_argument('--reverse_direction', action='store_true')
  parser.add_argument('--logging', type=int, default=20, choices=[10,20,30,40])
  args = parser.parse_args()
  
  logging.basicConfig(level=args.logging, format='%(levelname)s: %(message)s')

  # Using cv2.imread instead of scipy.misc because cv2 correctly processes 16bits.
  assert op.exists(args.in_image_path), args.in_image_path
  in_image = cv2.imread(args.in_image_path, -1)

  out_image = warp(in_image, args.camera, args.pose_id,
      dilation_radius=args.dilation_radius,
      reverse_direction=args.reverse_direction)

  if args.out_image_path:
    cv2.imwrite(args.out_image_path, out_image)

