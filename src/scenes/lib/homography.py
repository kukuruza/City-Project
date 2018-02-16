import os.path as op
import numpy as np
from time import time
import logging
from scene import Video
from conventions import read_azimuth_image



class Homography:
  ''' Takes care of homography-related caching.
  Loads poses, homography, azimuth maps (piling up).
  '''

  def __init__(self):
    self.cached_pose = {}
    self.cached_azimuth_map = {}

  def _getPose(self, imagefile):    
    # Get Pose for imagefile
    if imagefile in self.cached_pose:
      pose = self.cached_pose[imagefile]
      logging.info('Took pose from cache for %s' % imagefile)
    else:
      # Only pose for an imagefile is cached now.
      # New imagefile means reading camera json.
      pose = Video.from_imagefile(imagefile).pose
      self.cached_pose = {imagefile: pose}  # Only one item in cache.
      logging.info('Created pose for %s' % imagefile)
    return pose

  def getHfromImagefile(self, imagefile):
    #assert 0, 'TODO: implement videos'
    pose = self._getPose(imagefile)
    if pose is None:
      return None
    elif 'H_pose_to_map' not in pose:
      logging.warning('H is not in the pose %s for camera %s' %
          (pose.pose_id, pose.camera_id))
      return None
    else:
      H = np.asarray(pose['H_pose_to_map']).reshape((3,3))
      logging.debug('H_pose_to_map:\n%s' % str(H))
      return H

  def getAzimuthMapFromImagefile(self, imagefile):
    pose = self._getPose(imagefile)
    if pose is None:
      return None
    azimuth_map_path = op.join(pose.get_pose_dir(),
        '4azimuth-map%d/azimuth-top-down-from-camera.png' % pose.map_id)
    if azimuth_map_path in self.cached_azimuth_map:
      logging.info('Found azimuth_map_path %s in cache' % azimuth_map_path)
      return self.cached_azimuth_map[azimuth_map_path]
    if not op.exists(azimuth_map_path):
      logging.info('azimuth_map_path %s does not exist' % azimuth_map_path)
      return None
    else:
      azimuth_map, azimuth_mask = read_azimuth_image(azimuth_map_path)
      self.cached_azimuth_map[azimuth_map_path] = (azimuth_map, azimuth_mask)
      logging.info('Loaded azimuth_map_path %s.' % azimuth_map_path)
      return azimuth_map, azimuth_mask


def transformPoint():
  assert 0, 'The function moved to warp.py.'

def getFrameFlattening(H, y_frame, x_frame):
  ''' Compute flattening == sin(pitch) for a point in a frame. '''

  def _getMapEllipse(H, y_frame, x_frame):
    assert H is not None
    p_frame = np.asarray([[x_frame],[y_frame],[1.]])
    p_frame_dx = np.asarray([[x_frame + 1.],[y_frame],[1.]])
    p_frame_dy = np.asarray([[x_frame],[y_frame + 1.],[1.]])
    p_map = np.matmul(H, p_frame)
    p_map /= p_map[2]
    p_map_dx = np.matmul(H, p_frame_dx)
    p_map_dx /= p_map_dx[2]
    p_map_dy = np.matmul(H, p_frame_dy)
    p_map_dy /= p_map_dy[2]
    return p_map_dx - p_map, p_map_dy - p_map

  assert H is not None
  dx, dy = _getMapEllipse(H, y_frame, x_frame)
  flattening = np.linalg.norm(dx, ord=2) / np.linalg.norm(dy, ord=2)
  #logging.debug('Flattening: %.2f' % flattening)
  return flattening


def getFramePxlsInMeter(H, pxls_in_meter, y_frame, x_frame):
  ''' Compute size (in meters) for a point in a frame. '''

  def _getMapDxMeters(H, y_frame, x_frame):
    assert H is not None
    p_frame = np.asarray([[x_frame],[y_frame],[1.]])
    p_frame_dx = np.asarray([[x_frame + 1.],[y_frame],[1.]])
    p_map = np.matmul(H, p_frame)
    p_map /= p_map[2]
    p_map_dx = np.matmul(H, p_frame_dx)
    p_map_dx /= p_map_dx[2]
    return p_map_dx - p_map

  assert H is not None
  dx_pxl = _getMapDxMeters(H, y_frame, x_frame)
  dx_meters = pxls_in_meter / np.linalg.norm(dx_pxl, ord=2)
  #logging.debug('Size, meters: %.2f' % dx_meters)
  return dx_meters

