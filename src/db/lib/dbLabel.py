import os, sys, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import numpy as np
import logging
from scipy.cluster import hierarchy
from dbUtilities import bbox2roi, roi2bbox
from helperDb import deleteCar, carField
from helperKeys import getCalibration
from helperImg import ReaderVideo
from scipy.misc import imresize, imread
from scenes.lib.cvScrollZoomWindow import Window
from scenes.lib.homography import Homography, transformPoint
import cv2



def add_parsers(subparsers):
  labelAzimuthParser(subparsers)


class AzimuthWindow(Window):
  ''' Use Shift + left button to choose azimuth. '''

  def __init__(self, img, x, y, axis_x, axis_y, winsize=500):
    Window.__init__(self, img, winsize, name='azimuth', num_zoom_levels=2)
    self.is_just_a_suggestion = False  # Used to pick color.
    self.yaw = None
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
      self.is_just_a_suggestion = False
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
    color = (255,0,0)
    cv2.ellipse(self.cached_zoomed_img, 
        (int(self.x), int(self.y)), (int(self.axis_x * 0.6), int(self.axis_y * 0.6)),
        startAngle=0, endAngle=360, angle=0, color=color, thickness=2)
    if self.yaw:
      y1 = self.y - self.axis_y * np.cos(self.yaw * np.pi / 180.) * 1.2
      x1 = self.x + self.axis_x * np.sin(self.yaw * np.pi / 180.) * 1.2
      cv2.arrowedLine(self.cached_zoomed_img,
          (int(self.x),int(self.y)), (int(x1),int(y1)), color=color, thickness=2)
      postfix = '(suggested by azimuth map)' if self.is_just_a_suggestion else ''
      cv2.putText(self.cached_zoomed_img, 'yaw %.0f %s' % (self.yaw, postfix), (10, 70),
          cv2.FONT_HERSHEY_SIMPLEX, 1., color, 2)


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


def _getFlatteningFromImagefile(homography, imagefile, y_frame, x_frame):
  H = homography.getHfromImagefile(imagefile)
  if H is not None:
    dx, dy = _getMapEllipse(H, y_frame, x_frame)
    flattening = np.linalg.norm(dx, ord=2) / np.linalg.norm(dy, ord=2)
    logging.info('Flattening: %.2f' % flattening)
  else:
    flattening = 1.
  return flattening


def _getAzimuthSuggestionFromMap(homography, imagefile, y_frame, x_frame):

  def _crop(img, x, y, radius):
    ''' Crop with attention to the borders. '''
    y, x, radius = int(y), int(x), int(radius)
    min_x = max(0, x - radius)
    min_y = max(0, y - radius)
    center_x = x - min_x
    center_y = y - min_y
    max_x = min(img.shape[1], x + radius)
    max_y = min(img.shape[0], y + radius)
    crop = img[min_y:max_y, min_x:max_x]
    return crop, (center_x, center_y)

  def _getDistToPoint(img, x, y):
    X, Y = img.shape[1], img.shape[0]
    delta_x_1D = np.arange(X) - x
    delta_y_1D = np.arange(Y) - y
    delta_x = np.dot( np.ones((Y,1)), delta_x_1D[np.newaxis,:] ).astype(float)
    delta_y = np.dot( delta_y_1D[:,np.newaxis], np.ones((1,X)) ).astype(float)
    dist = np.sqrt(np.square(delta_x) + np.square(delta_y))
    return dist

  def _suggestionFromImage(arr, mask, x, y, pxls_in_meters):
    RADIUS_METERS = 2.
    radius = RADIUS_METERS * pxls_in_meter
    degree_threshold = 10.  # Degrees.
    # First crop to reduce computations.
    arr, _ = _crop(arr, x, y, radius)
    mask, (x, y) = _crop(mask, x, y, radius)
    # Flatten, apply the mask, and sort the array based on distance to (x, y).
    dist = _getDistToPoint(arr, x, y)
    dist_ind = dist[mask].argsort()
    if dist_ind.size == 0:
      return None
    sorted_arr = arr[mask][dist_ind]
    # Cluster based on degree.
    z = hierarchy.linkage(sorted_arr[:,np.newaxis])
    clusters = hierarchy.fcluster(z, 10., criterion="distance").tolist()
    elems = [clusters.index(i) for i in range(1,max(clusters)+1)]
    elems.sort()  # So that coord-wise closer points come first.
    suggestions = [sorted_arr[elem] for elem in elems]
    logging.info('Got suggestions %s from radius of %d pxl and threshold of %.0f deg.' %
       (str(suggestions), radius, degree_threshold))
    # # Debugging - show the cropped image.
    # X, Y = mask.shape[1], mask.shape[0]
    # coords_x = np.dot( np.ones((Y,1)), np.arange(X)[np.newaxis,:] )
    # coords_y = np.dot( np.arange(Y)[:,np.newaxis], np.ones((1,X)) )
    # display = arr.astype(np.uint8)
    # display[np.bitwise_not(mask)] = 0
    # cv2.circle(display, (int(x), int(y)), radius=3, color=(255,), thickness=2)
    # for elem in elems:
    #   x = coords_x[mask][dist_ind][elem]
    #   y = coords_y[mask][dist_ind][elem]
    #   cv2.circle(display, (int(x), int(y)), radius=2, color=(255,), thickness=1)
    #   print (x, y, sorted_arr[elem])
    # cv2.imshow('debug', display)
    # cv2.waitKey(-1)
    return suggestions

  azimuth_map, azimuth_mask = homography.getAzimuthMapFromImagefile(imagefile)
  if azimuth_map is None:
    return None
  H = homography.getHfromImagefile(imagefile)
  if H is None:
    return None
  x_map, y_map = transformPoint(H, x_frame, y_frame)
  pose = homography._getPose(imagefile)
  pxls_in_meter = pose.map['pxls_in_meter'] if pose is not None else None
  suggestions = _suggestionFromImage(azimuth_map, azimuth_mask, x_map, y_map, pxls_in_meter)
  return suggestions


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

  homography = Homography()

  button = 0
  index_car = 0
  another_car = True
  char_list = []
  while button != 27:
    go_next_car = False
    update_yaw_in_db = False

    if another_car:
      another_car = False
      suggestions = None
      i_suggestion = None

      logging.info(' ')
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

      flattening = _getFlatteningFromImagefile(homography, imagefile, y, x)
      axis_x = np.linalg.norm(np.asarray(bbox[2:4]), ord=2)
      axis_y = axis_x * flattening

      display = image_reader.imread(imagefile)[:,:,::-1].copy()
      window = AzimuthWindow(display, x, y, axis_x, axis_y, winsize=args.winsize)
      if yaw is not None:
        logging.info('Yaw is: %.0f' % yaw)
        window.yaw = yaw
      else:
        suggestions = _getAzimuthSuggestionFromMap(homography, imagefile, y, x)
        if suggestions is not None:
          i_suggestion = 0
          window.is_just_a_suggestion = True
          window.yaw = suggestions[i_suggestion]
      window.update_cached_zoomed_img()
      window.redraw()

    button = cv2.waitKey(50)

    if button == keys['del']:
      c.execute('UPDATE cars SET yaw=NULL WHERE id=?', (carid,))
      logging.info('Yaw is deleted.')
      go_next_car = True
      char_list = []

    # Space iterates between suggestions.
    if button == ord(' ') and suggestions is not None and len(suggestions) > 1:
      i_suggestion = (i_suggestion + 1) % len(suggestions)
      logging.info('Go to suggestion %d out of %d' % (i_suggestion, len(suggestions)))
      window.is_just_a_suggestion = True
      window.yaw = suggestions[i_suggestion]
      window.update_cached_zoomed_img()
      window.redraw()

    # Entry in keyboard.
    if button >= ord('0') and button <= ord('9') or button == ord('.'):
      char_list += chr(button)
      logging.debug('Added %s character to number and got %s' %
          (chr(button), ''.join(char_list)))
    # Enter accepts a Suggestion, GUI, or keyboard entry.
    elif button == 13:      
      if char_list:  # After keyboard entry.
        number_str = ''.join(char_list)
        char_list = []
        try:
          logging.info('Accepting entry from the keyboard.')
          yaw = float(number_str)
          update_yaw_in_db = True
          go_next_car = True
        except ValueError:
          logging.warning('Could not convert entered %s to number.' % number_str)
          continue
      elif suggestions is not None:  # Accept a suggestion.
        logging.info('Accepting the suggestion.')
        yaw = window.yaw
        update_yaw_in_db = True
        go_next_car = True
      else:  # Just navigation.
        logging.info('A navigation Enter.')
        go_next_car = True
    # Entry in GUI.
    elif window.selected == True:
      logging.info('Accepting entry from GUI.')
      yaw = window.yaw
      update_yaw_in_db = True
      go_next_car = True
    # No entry:
    else:
      yaw = None

    # Entry happened one way or the other. Update the yaw and go to the next car.
    if update_yaw_in_db:
      c.execute('UPDATE cars SET yaw=? WHERE id=?', (yaw, carid))
      logging.info('Yaw is assigned to %.f' % yaw)

    # Navigation.
    if button == keys['left']:
      logging.debug ('prev car')
      if index_car > 0:
        index_car -= 1
        another_car = True
      else:
        logging.warning('Already at the first car.')
    elif button == keys['right'] or go_next_car == True:
      logging.debug ('next car')
      if index_car < len(car_entries) - 1:
        index_car += 1
        another_car = True
      else:
        logging.warning('Already at the last car. Press Esc to save and exit.')


