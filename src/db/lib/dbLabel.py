import os, sys, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import numpy as np
import logging
from dbUtilities import bbox2roi, roi2bbox, drawRoi, drawScoredRoi, drawScoredPolygon
from dbUtilities import getCenter
from helperDb import deleteCar, carField
from helperKeys import getCalibration
from helperImg import ReaderVideo
from scipy.misc import imresize
from scenes.lib.cvScrollZoomWindow import Window
from scenes.lib.camera import VideoHomography
import cv2



def add_parsers(subparsers):
  labelAzimuthParser(subparsers)


class AzimuthWindow(Window):
  ''' Use mouse left button and wheel to navigate,
  shift + left button to choose azimuth.
  '''

  def __init__(self, img, x, y, axis_x, axis_y, yaw=None, winsize=500, name='azimuth'):
    self.x, self.y = x, y
    self.axis_x, self.axis_y = axis_x, axis_y
    self.yaw = yaw
    self.selected = False
    Window.__init__(self, img, winsize, name, num_zoom_levels=2)

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
      self.yaw = np.arctan2((x - self.x) / self.axis_x, 
                           -(y - self.y) / self.axis_y) * 180. / np.pi
      logging.debug('%s, yaw is at %0.f' % (self.name, self.yaw))
      self.update_cached_zoomed_img()
      self.redraw()
      if event == cv2.EVENT_LBUTTONDOWN:
        self.selected = True
        logging.debug('%s: registered shift + mouse press.' % self.name)

  def update_cached_zoomed_img(self):
    Window.update_cached_zoomed_img(self)
    cv2.ellipse(self.cached_zoomed_img, (int(self.x), int(self.y)), 
        (int(self.axis_x * 0.75), int(self.axis_y * 0.75)),
        startAngle=0, endAngle=360, angle=0, color=(255,0,0), thickness=2)
    if self.yaw:
      y1 = self.y - self.axis_y * np.cos(self.yaw * np.pi / 180.) * 1.5
      x1 = self.x + self.axis_x * np.sin(self.yaw * np.pi / 180.) * 1.5
      cv2.arrowedLine(self.cached_zoomed_img, (int(self.x),int(self.y)), (int(x1),int(y1)),
          color=(255,0,0), thickness=2)


def _getFlatteningFromImagefile(videoH, imagefile, y_frame, x_frame):
  H = videoH.getHfromImagefile(imagefile)
  if H is not None:
    p_frame = np.asarray([[x_frame],[y_frame],[1.]])
    p_frame_dx = np.asarray([[x_frame + 1.],[y_frame],[1.]])
    p_frame_dy = np.asarray([[x_frame],[y_frame + 1.],[1.]])
    p_map = np.matmul(H, p_frame)
    p_map /= p_map[2]
    p_map_dx = np.matmul(H, p_frame_dx)
    p_map_dx /= p_map_dx[2]
    p_map_dy = np.matmul(H, p_frame_dy)
    p_map_dy /= p_map_dy[2]
    dpx_norm = np.linalg.norm(p_map_dx - p_map, ord=2)
    dpy_norm = np.linalg.norm(p_map_dy - p_map, ord=2)
    flattening = dpx_norm / dpy_norm
    logging.info('Flattening: %.2f' % flattening)
  else:
    flattening = 1.
  return flattening


def labelAzimuthParser(subparsers):
  parser = subparsers.add_parser('labelAzimuth',
    description='''Go through cars and label yaw (azimuth)
    by either accepting one of the close yaw values from a map,
    or by assigning a value manually.''')
  parser.set_defaults(func=labelAzimuth)
  parser.add_argument('--display_scale', type=float, default=1.)
  parser.add_argument('--shuffle', action='store_true')
  parser.add_argument('--load_labelled_too', action='store_true')

def labelAzimuth (c, args):
  logging.info ('==== labelAzimuth ====')

  image_reader = ReaderVideo()
  keys = getCalibration()

  if args.load_labelled_too:
    c.execute('SELECT * FROM cars WHERE yaw = NULL')
  else:
    c.execute('SELECT * FROM cars')
  car_entries = c.fetchall()
  logging.info('Found %d objects in db.' % len(car_entries))

  if args.shuffle:
    np.random.shuffle(car_entries)

  videoH = VideoHomography()

  button = 0
  index_car = 0
  prev_index_car = None
  char_list = []
  while button != 27:

    if prev_index_car is None or index_car != prev_index_car:
      prev_index_car = index_car

      car_entry = car_entries[index_car]
      carid     = carField(car_entry, 'id')
      bbox      = carField(car_entry, 'bbox')
      roi       = carField(car_entry, 'roi')
      imagefile = carField(car_entry, 'imagefile')
      # Update yaw inside the loop in case it was just assigned.
      c.execute('SELECT yaw FROM cars WHERE id=?', (carid,))
      yaw, = c.fetchone()

      y, x = roi[0] * 0.3 + roi[2] * 0.7, roi[1] * 0.5 + roi[3] * 0.5
      flattening = _getFlatteningFromImagefile(videoH, imagefile, y, x)
      axis_x = np.linalg.norm(np.asarray(bbox[2:4]), ord=2)
      axis_y = axis_x * flattening
      logging.info('Ellipse: x y axis_x axis_y:  %.1f %.1f %.1f %.1f' % (x, y, axis_x, axis_y))

      display = image_reader.imread(imagefile)[:,:,::-1].copy()
#      display = imresize(display, args.display_scale)
      font = cv2.FONT_HERSHEY_SIMPLEX
      if yaw is None:
        logging.info('Yaw is None.')
      if yaw is not None:
        logging.info('Yaw is: %.0f' % yaw)
        print display.shape, 'yaw: %.0f' % yaw
        cv2.putText(display, 'yaw: %.0f' % yaw, (10, 20), font, 0.5, (255,255,255), 2)
      window = AzimuthWindow(display, x, y, axis_x, axis_y, yaw)

    button = cv2.waitKey(50)

    # Navigation.
    if button == keys['left']:
      logging.debug ('prev car')
      if index_car > 0:
        index_car -= 1
      else:
        logging.warning('Already at the first car.')
    elif button == keys['right']:
      logging.debug ('next car')
      if index_car < len(car_entries):
        index_car += 1
      else:
        logging.warning('Already at the last car. Press Esc to save and exit.')

    elif button == keys['del']:
      c.execute('UPDATE cars SET yaw=NULL WHERE id=?', (carid,))
      logging.info('Yaw is deleted.')
      index_car += 1
      char_list = []

    # Entry in GUI.
    if window.selected == True:
      yaw = window.yaw
      print ('Yaw set in GUI.')
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
      except ValueError:
        logging.warning('Could not convert entered %s to number.' % number_str)
        continue
    # No entry:
    else:
      yaw = None

    # Entry happened one way or the other. Update the yaw and go to the next car.
    if yaw is not None:
      c.execute('UPDATE cars SET yaw=? WHERE id=?', (yaw, carid))
      logging.info('Yaw is assigned to %.f' % yaw)
      index_car += 1

