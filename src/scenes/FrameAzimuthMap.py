import os, os.path as op
import numpy as np
import logging
from glob import glob
import argparse
import cv2
import subprocess
from skimage.measure import label
from Warp import warp
from scenes.lib.camera import Pose


def read_azimuth_image(azimuth_path):
  ''' Take care of reading the image and respect the conventions. '''

  assert op.exists(azimuth_path), azimuth_path
  azimuth = cv2.imread(azimuth_path, -1)
  assert azimuth is not None
  # Mask is in the alpha channel, the other 3 channels are the same value.
  mask = azimuth[:,:,3] > 0
  azimuth = azimuth[:,:,0].astype(float)
  # By convention, azimuth angles are divided by 2 before written to image.
  azimuth *= 2
  return azimuth, mask


def write_azimuth_image(azimuth_path, azimuth, mask=None):
  ''' Take care of wrting the image and respect the conventions. '''

  # By convention, azimuth angles are divided by 2 before written to image.
  azimuth = azimuth.copy() / 2.

  # By convention to be human-friendly, write as 8bit.
  azimuth = azimuth.astype(np.uint8)

  assert len(azimuth.shape) == 2, 'Need grayscale azimuth.'
  if mask is None:
    mask = np.ones(azimuth.shape, dtype=np.uint8) * 255
  else:
    assert mask.shape == azimuth.shape
    mask = mask.astype(np.uint8)
    mask[mask > 0] = 255

  # Mask is in the alpha channel, the other 3 channels are the same value.
  azimuth = np.stack((azimuth, azimuth, azimuth, mask), axis=-1)
  cv2.imwrite(azimuth_path, azimuth)
  

if __name__ == "__main__":

  parser = argparse.ArgumentParser(description=
      '''The pipeline for computing azimuth maps.
      All azimuth are ''')
  parser.add_argument('--camera_id', required=True, default="cam572")
  parser.add_argument('--pose_id', type=int, default=0)
  parser.add_argument('--map_id', type=int, help='If not set, will use pose["best_map_id"]')
  parser.add_argument('--steps', nargs='+',
      choices=['2topdown', 'compute_azimuth', 'delta', '2frame'])
  parser.add_argument('--logging', type=int, default=20, choices=[10,20,30,40])
  args = parser.parse_args()
  
  logging.basicConfig(level=args.logging, format='%(levelname)s: %(message)s')

  pose = Pose(camera_id=args.camera_id, pose_id=args.pose_id, map_id=args.map_id)

  pose_dir = pose.get_pose_dir()
  for_azimuth_dir = op.join(pose_dir, '4azimuth-map%d' % pose.map_id)
  if not op.exists(for_azimuth_dir):
    os.makedirs(for_azimuth_dir)

  if args.steps is None or '2topdown' in args.steps:
    lane_paths = glob(op.join(for_azimuth_dir, 'lanes*16b.png'))
    print ('Found %d lane images' % len(lane_paths))

    for lane_path in lane_paths:
      print lane_path
      assert op.exists(lane_path), lane_path
      in_lane = cv2.imread(lane_path, -1)

      # Find the min radius that does not ruin lanes.
      counts = []
      for dilation_radius in range(5):
        warped_lane = warp(in_lane, args.camera, args.pose_id,
            dilation_radius=dilation_radius)
        _, count = label((warped_lane > 0).astype(int), connectivity=2, return_num=True)
        counts.append(count)
      print ('Lanes segments counts for different dilation', counts)
      first_index_of_min_count = counts.index(min(counts))
  
      # Do again with the optimal radius, and write to disk.
      dilation_radius = range(5)[first_index_of_min_count]
      print ('Will use dilation radius %d' % dilation_radius)
      warped_lane = warp(in_lane, args.camera_id, args.pose_id,
          dilation_radius=dilation_radius)
      warped_lane_path = op.splitext(lane_path)[0] + '-warped.png'
      cv2.imwrite(warped_lane_path, warped_lane)
 
  # Calculate azimuth on the top-down view.
  if args.steps is None or 'compute_azimuth' in args.steps:
    s = '''"cd(fullfile(getenv('CITY_PATH'), 'src/scenes/lib')); 
            ComputeAzimuthMap('%s/4azimuth/lanes*warped.png', '%s/4azimuth/azimuth-top-down.png');
            exit;" ''' % (pose_dir, pose_dir)
    command = ['matlab', '-nodisplay', '-r', s]
    returncode = subprocess.call (command, shell=False)#, stdout=FNULL, stderr=FNULL)

  if args.steps is None or 'delta' in args.steps:
    print ('Creating delta azimuth for top-down view.')
    azimuth_top_down_path = op.join(pose_dir, '4azimuth/azimuth-top-down.png')
    azimuth_top_down, mask_top_down = read_azimuth_image(azimuth_top_down_path)
   
    # Camera can see ech point at a certain angle.
    origin = pose.map['map_origin']
    X, Y = azimuth_top_down.shape[1], azimuth_top_down.shape[0]
    delta_x_1D = np.arange(X) - origin['x']
    delta_y_1D = np.arange(Y) - origin['y']
    delta_x = np.dot( np.ones((Y,1)), delta_x_1D[np.newaxis,:] ).astype(float)
    delta_y = np.dot( delta_y_1D[:,np.newaxis], np.ones((1,X)) ).astype(float)
    delta_azimuth = np.arctan2 (delta_x, -delta_y)  # 0 is north, 90 is east.
    # From [-pi, pi] to [0 360]
    delta_azimuth = np.mod( (delta_azimuth * 180. / np.pi), 360. )
    # Write for debugging.
    delta_azimuth_path = op.join(for_azimuth_dir, 'azimuth-top-down-delta.png')
    write_azimuth_image(delta_azimuth_path, delta_azimuth)
    # Top-down azimuth in camera point of view, 0 is north, 90 is east.
    azimuth_top_down = np.mod(azimuth_top_down - delta_azimuth, 360.)
    azimuth_top_down_path = op.join(for_azimuth_dir, 'azimuth-top-down-from-camera.png')
    write_azimuth_image(azimuth_top_down_path, azimuth_top_down, mask_top_down)

  if args.steps is None or '2frame' in args.steps:
    print ('Warping from top-down view to frame view.')
    azimuth_top_down_path = op.join(pose_dir, '4azimuth/azimuth-top-down-from-camera.png')
    azimuth_top_down, mask_top_down = read_azimuth_image(azimuth_top_down_path)
    azimuth_frame = warp(azimuth_top_down, args.camera_id, args.pose_id,
          dilation_radius=0, reverse_direction=True)
    mask_frame = warp(mask_top_down.astype(float), args.camera_id, args.pose_id,
          dilation_radius=0, reverse_direction=True) > 0.5
    azimuth_frame_path = op.join(pose_dir, 'azimuth-frame.png')
    write_azimuth_image(azimuth_frame_path, azimuth_frame, mask_frame)

  

