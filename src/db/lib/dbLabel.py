import os, sys, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import numpy as np
import logging
from dbUtilities import bbox2roi, roi2bbox, drawRoi, drawScoredRoi, drawScoredPolygon
from dbUtilities import getCenter
from helperDb import deleteCar, carField
from helperKeys import getCalibration
from helperImg import ReaderVideo
from scipy.misc import imresize, imread
from scenes.lib.cvScrollZoomWindow import Window
from scenes.lib.camera import createPoseFromImagefile
from scenes.lib.azimuth import read_azimuth_image
import cv2



def add_parsers(subparsers):
  labelAzimuthParser(subparsers)


class _VideoHomography:

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
      pose = createPoseFromImagefile(imagefile)
      self.cached_pose = {imagefile: pose}  # Only one item in cache.
      logging.info('Created pose for %s' % imagefile)
    return pose

  def getHfromImagefile(self, imagefile):
    pose = self._getPose(imagefile)
    if pose is None:
      return None
    elif 'H_frame_to_map' not in pose['maps'][pose.map_id]:
      logging.warning('H is not in the pose %s for camera %s' %
          (pose.pose_id, pose.camera_id))
      return None
    else:
      H = np.asarray(pose['maps'][pose.map_id]['H_frame_to_map']).reshape((3,3))
      logging.debug('H_frame_to_map:\n%s' % str(H))
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


class AzimuthWindow(Window):
  ''' Use Shift + left button to choose azimuth. '''

  def __init__(self, img, x, y, axis_x, axis_y, yaw=None, winsize=500, name='azimuth'):
    Window.__init__(self, img, winsize, name, num_zoom_levels=2)
    self.yaw = yaw
    self.selected = False
    self.x, self.y = self.image_to_zoomedimage_coords(x, y)
    self.axis_x = axis_x * self.get_zoom(self.zoom_level)
    self.axis_y = axis_y * self.get_zoom(self.zoom_level)

  def mouseHandler(self, event, x, y, flags, params):

    # Call navigation handler from the base class.
    Window.mouseHandler(self, event, x, y, flags, params)

    # Display and maybe select azimuth.
    #   flags == 16 <=> Shift + no mouse press
    #   flags == 17 <=> Shift + left button down
    if (event == cv2.EVENT_MOUSEMOVE and flags == 16 or
        event == cv2.EVENT_LBUTTONDOWN and flags == 17):
      logging.debug('%s: registered shift + mouse move and maybe press.' % self.name)
      # 0 is north, 90 is east.
      self.yaw = (np.arctan2((x - self.x) / self.axis_x, 
                            -(y - self.y) / self.axis_y) * 180. / np.pi) % 360
      logging.debug('%s, yaw is at %0.f' % (self.name, self.yaw))
      self.update_cached_zoomed_img()
      self.redraw()
      if event == cv2.EVENT_LBUTTONDOWN:
        self.selected = True
        logging.debug('%s: registered shift + mouse press.' % self.name)

  def update_cached_zoomed_img(self):
    Window.update_cached_zoomed_img(self)
    cv2.ellipse(self.cached_zoomed_img, 
        (int(self.x), int(self.y)), (int(self.axis_x * 0.6), int(self.axis_y * 0.6)),
        startAngle=0, endAngle=360, angle=0, color=(255,0,0), thickness=2)
    if self.yaw:
      y1 = self.y - self.axis_y * np.cos(self.yaw * np.pi / 180.) * 1.2
      x1 = self.x + self.axis_x * np.sin(self.yaw * np.pi / 180.) * 1.2
      cv2.arrowedLine(self.cached_zoomed_img,
          (int(self.x),int(self.y)), (int(x1),int(y1)),
          color=(255,0,0), thickness=2)


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


def _getFlatteningFromImagefile(videoH, imagefile, y_frame, x_frame):
  H = videoH.getHfromImagefile(imagefile)
  if H is not None:
    dx, dy = _getMapEllipse(H, y_frame, x_frame)
    flattening = np.linalg.norm(dx, ord=2) / np.linalg.norm(dy, ord=2)
    logging.info('Flattening: %.2f' % flattening)
  else:
    flattening = 1.
  return flattening


def _getAzimuthSuggestionFromMap(videoH, imagefile, y_frame, x_frame):
  azimuth_map, azimuth_mask = videoH.getAzimuthMapFromImagefile(imagefile)
  if azimuth_map is None:
    return None
  H = videoH.getHfromImagefile(imagefile)
  if H is None:
    return None
  # Find the point on top-down view.
  p_frame = np.asarray([[x_frame],[y_frame],[1.]])
  p_map = np.matmul(H, p_frame)
  p_map /= p_map[2]
  x_map, y_map = p_map[0], p_map[1]
  print x_map, y_map
  # Find points in a radius
  def _closest_nonzero_point(arr, mask, x, y):
    arr[np.bitwise_not(mask)] = -1
    X, Y = arr.shape[1], arr.shape[0]
    delta_x_1D = np.arange(X) - x
    delta_y_1D = np.arange(Y) - y
    delta_x = np.dot( np.ones((Y,1)), delta_x_1D[np.newaxis,:] ).astype(float)
    delta_y = np.dot( delta_y_1D[:,np.newaxis], np.ones((1,X)) ).astype(float)
    dist = np.sqrt(np.square(delta_x) + np.square(delta_y))
    #for ix in range(X):
    #  for iy in range(Y):
    #    if dist[iy,ix] < 10 and azimuth_mask[iy,ix] == True:
    #      print iy, ix, arr[iy,ix]
    #print ('Done')
    dist_ind = dist.flatten().argsort()
    sorted_arr = arr.flatten()[dist_ind]
    return sorted_arr[np.nonzero(sorted_arr > -1)][0]
  azimuth = _closest_nonzero_point(azimuth_map, azimuth_mask, x_map, y_map)
  # Instead of nonzero, use azimuth_mask
  print ('azimuth', azimuth)
  return azimuth


def labelAzimuthParser(subparsers):
  parser = subparsers.add_parser('labelAzimuth',
    description='''Go through cars and label yaw (azimuth)
    by either accepting one of the close yaw values from a map,
    or by assigning a value manually.''')
  parser.set_defaults(func=labelAzimuth)
  parser.add_argument('--display_scale', type=float, default=1.)
  parser.add_argument('--winsize', type=int, default=500)
  parser.add_argument('--shuffle', action='store_true')
  parser.add_argument('--car_constraint', default='1')

def labelAzimuth (c, args):
  logging.info ('==== labelAzimuth ====')

  image_reader = ReaderVideo()
  keys = getCalibration()

  c.execute('SELECT * FROM cars WHERE (%s)' % args.car_constraint)
  car_entries = c.fetchall()
  logging.info('Found %d objects in db.' % len(car_entries))
  if len(car_entries) == 0:
    return

  if args.shuffle:
    np.random.shuffle(car_entries)

  videoH = _VideoHomography()

  button = 0
  index_car = 0
  do_draw = True
  char_list = []
  while button != 27:
    go_next_car = False
    update_yaw_in_db = False

    if do_draw:
      do_draw = False

      logging.info('Car %d out of %d' % (index_car, len(car_entries)))
      car_entry = car_entries[index_car]
      carid     = carField(car_entry, 'id')
      bbox      = carField(car_entry, 'bbox')
      roi       = carField(car_entry, 'roi')
      imagefile = carField(car_entry, 'imagefile')
      # Update yaw inside the loop in case it was just assigned.
      c.execute('SELECT yaw FROM cars WHERE id=?', (carid,))
      yaw, = c.fetchone()

      y, x = roi[0] * 0.3 + roi[2] * 0.7, roi[1] * 0.5 + roi[3] * 0.5

      if yaw is None:
        yaw = _getAzimuthSuggestionFromMap(videoH, imagefile, y, x)

      flattening = _getFlatteningFromImagefile(videoH, imagefile, y, x)
      axis_x = np.linalg.norm(np.asarray(bbox[2:4]), ord=2)
      axis_y = axis_x * flattening

      display = image_reader.imread(imagefile)[:,:,::-1].copy()
      if yaw is None:
        logging.info('Yaw is None.')
      if yaw is not None:
        logging.info('Yaw is: %.0f' % yaw)
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(display, 'yaw: %.0f' % yaw, (10, 20), font, 0.5, (255,255,255), 2)
      window = AzimuthWindow(display, x, y, axis_x, axis_y, yaw, winsize=args.winsize)
      window.update_cached_zoomed_img()
      window.redraw()

    button = cv2.waitKey(50)

    if button == keys['del']:
      c.execute('UPDATE cars SET yaw=NULL WHERE id=?', (carid,))
      logging.info('Yaw is deleted.')
      go_next_car = True
      char_list = []

    # Entry in GUI.
    if window.selected == True:
      yaw = window.yaw
      update_yaw_in_db = True
    # Entry in keyboard.
    elif button >= ord('0') and button <= ord('9') or button == ord('.'):
      char_list += chr(button)
      logging.debug('Added %s character to number and got %s' %
          (chr(button), ''.join(char_list)))
    elif button == 13 and char_list:  # enter.
      number_str = ''.join(char_list)
      char_list = []
      try:
        yaw = float(number_str)
        update_yaw_in_db = True
      except ValueError:
        logging.warning('Could not convert entered %s to number.' % number_str)
        continue
    # No entry:
    else:
      yaw = None

    # Entry happened one way or the other. Update the yaw and go to the next car.
    if update_yaw_in_db:
      c.execute('UPDATE cars SET yaw=? WHERE id=?', (yaw, carid))
      logging.info('Yaw is assigned to %.f' % yaw)
      go_next_car = True

    # Navigation.
    if button == keys['left']:
      logging.debug ('prev car')
      if index_car > 0:
        index_car -= 1
        do_draw = True
      else:
        logging.warning('Already at the first car.')
    elif button == keys['right'] or go_next_car == True:
      logging.debug ('next car')
      if index_car < len(car_entries) - 1:
        index_car += 1
        do_draw = True
      else:
        logging.warning('Already at the last car. Press Esc to save and exit.')


