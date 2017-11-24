import sys, os, os.path as op
import logging
import shutil
import argparse
import numpy as np
import cv2
import simplejson as json
from scipy.misc import imread
from lib.cvScrollZoomWindow import Window
import colorsys

def get_random_color():
  ''' Get a random bright color. '''
  h,s,l = np.random.random(), 0.5 + np.random.random()/2.0, 0.4 + np.random.random()/5.0
  r,g,b = [int(256*i) for i in colorsys.hls_to_rgb(h,l,s)]
  return r,g,b


class MatchWindow(Window):
  ''' Use mouse left button and wheel to navigate, shift + left button
  to select points. Select a point in each image, and the match will be added.
  '''

  def __init__(self, img, winsize=500, name='display'):
    self.pointselected = None
    self.points = []  # (x, y), (b,g,r)
    Window.__init__(self, img, winsize, name)

  def mouseHandler(self, event, x, y, flags, params):

    # Call navigation handler from the base class.
    Window.mouseHandler(self, event, x, y, flags, params)

    # Select a point.
    if event == cv2.EVENT_LBUTTONDOWN and flags == 17:  # Shift
      logging.info('%s: registered mouse select press.' % self.name)
      x, y = self.window_to_image_coords(x, y)
      self.pointselected = (x, y)
      self.update_cached_zoomed_img()
      self.redraw()

  def update_cached_zoomed_img(self):
    Window.update_cached_zoomed_img(self)
    for (x, y), color in self.points:
      self._drawpoint(x, y, color)
    if self.pointselected is not None:
      self._drawpoint(self.pointselected[0], self.pointselected[1], (0,0,255))

  def _drawpoint(self, x, y, color):
    x, y = self.image_to_zoomedimage_coords(x, y)
    cv2.circle (self.cached_zoomed_img, (int(x), int(y)), 10, color, thickness=3)



def labelMatches (image_path1, image_path2, matches_path, 
                  winsize1=500, winsize2=500, backup_matches=True):

  # Read both images.
  assert op.exists(image_path1), image_path1
  assert op.exists(image_path2), image_path2
  img1 = imread(image_path1)
  img2 = imread(image_path2)
  assert img1 is not None
  assert img2 is not None

  name1 = op.splitext(op.basename(image_path1))[0]
  name2 = op.splitext(op.basename(image_path2))[0]
  if name1 == name2:
    name1 += '-1'
    name2 += '-2'
  window1 = MatchWindow(img1, args.winsize1, name=name1)
  window2 = MatchWindow(img2, args.winsize2, name=name2)

  # If already exists, we'll load existing matches.
  # pts_pairs is a list of tuples (x1, y1, x2, y2)
  if op.exists(matches_path):
    if backup_matches:
      backup_path = op.splitext(matches_path)[0] + '.backup.json'
      shutil.copyfile(matches_path, backup_path)
    with open(matches_path) as f:
      matches = json.load(f)
    for i in range(len(matches['frame']['x'])):
      color = get_random_color()
      window1.points.append(((matches['frame']['x'][i], matches['frame']['y'][i]), color))
      window2.points.append(((matches['map']['x'][i], matches['map']['y'][i]), color))
    window1.update_cached_zoomed_img()
    window2.update_cached_zoomed_img()
    window1.redraw()
    window2.redraw()

  BUTTON_ESCAPE = 27
  BUTTON_ENTER = 13
  button = -1
  while button != BUTTON_ESCAPE and button != BUTTON_ENTER:
    if window1.pointselected is not None and window2.pointselected is not None:
      logging.info('Adding a match')
      color = get_random_color()
      window1.points.append((window1.pointselected, color))
      window2.points.append((window2.pointselected, color))
      window1.pointselected = None
      window2.pointselected = None
      window1.update_cached_zoomed_img()
      window2.update_cached_zoomed_img()
      window1.redraw()
      window2.redraw()
    button = cv2.waitKey(50)

  # Save and exit.
  if button == BUTTON_ENTER:
    matches = {'frame': {'x': [], 'y': []}, 'map': {'x': [], 'y': []}}
    for p in window1.points:
      matches['frame']['x'].append(p[0][0])
      matches['frame']['y'].append(p[0][1])
    for p in window2.points:
      matches['map']['x'].append(p[0][0])
      matches['map']['y'].append(p[0][1])
    with open(matches_path, 'w') as f:
      f.write(json.dumps(matches, sort_keys=True, indent=2))
  elif button == BUTTON_ESCAPE:
    logging.info('Exiting without saving.')


if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('-1', '--image_path1', required=True)
  parser.add_argument('-2', '--image_path2', required=True)
  parser.add_argument('--matches_path', required=True)

  parser.add_argument('--winsize1', type=int, default=500)
  parser.add_argument('--winsize2', type=int, default=500)
  parser.add_argument('--logging', type=int, default=20, choices=[10,20,30,40])
  args = parser.parse_args()
  
  logging.basicConfig(level=args.logging, format='%(levelname)s: %(message)s')

  labelMatches (args.image_path1, args.image_path2, args.matches_path,
      winsize1=args.winsize1, winsize2=args.winsize2)
