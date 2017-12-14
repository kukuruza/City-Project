#!/usr/bin/env python
import os, os.path as op
import logging
import shutil
import argparse
import numpy as np
import cv2
import simplejson as json
from pprint import pprint, pformat
from scipy.misc import imread
from lib.cvWindow import Window
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



def labelMatches (img1, img2, matches_path, 
                  winsize1=500, winsize2=500, 
                  backup_matches=True, name1='frame', name2='map'):

  window1 = MatchWindow(img1, winsize1, name=name1)
  window2 = MatchWindow(img2, winsize2, name=name2)

  # If already exists, we'll load existing matches.
  # pts_pairs is a list of tuples (x1, y1, x2, y2)
  if op.exists(matches_path):
    if backup_matches:
      backup_path = op.splitext(matches_path)[0] + '.backup.json'
      shutil.copyfile(matches_path, backup_path)
    with open(matches_path) as f:
      matches = json.load(f)
    for i in range(len(matches[name1]['x'])):
      color = get_random_color()
      window1.points.append(((matches[name1]['x'][i], matches[name1]['y'][i]), color))
      window2.points.append(((matches[name2]['x'][i], matches[name2]['y'][i]), color))
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
    matches = {name1: {'x': [], 'y': []}, name2: {'x': [], 'y': []}}
    for p in window1.points:
      matches[name1]['x'].append(p[0][0])
      matches[name1]['y'].append(p[0][1])
    for p in window2.points:
      matches[name2]['x'].append(p[0][0])
      matches[name2]['y'].append(p[0][1])
    with open(matches_path, 'w') as f:
      f.write(json.dumps(matches, sort_keys=True, indent=2))
  elif button == BUTTON_ESCAPE:
    logging.info('Exiting without saving.')


def loadMatches(matches_path, name1, name2):

  # Load matches.
  assert op.exists(matches_path), matches_path
  matches = json.load(open(matches_path))
  logging.debug (pformat(matches, indent=2))
  src_pts = matches[name1]
  dst_pts = matches[name2]
  assert range(len(src_pts['x'])) == range(len(dst_pts['x']))
  assert range(len(src_pts['x'])) == range(len(src_pts['y']))
  assert range(len(dst_pts['x'])) == range(len(dst_pts['y']))

  # Matches as numpy array.
  N = range(len(src_pts['x']))
  src_pts = np.float32([ [src_pts['x'][i], src_pts['y'][i]] for i in N ])
  dst_pts = np.float32([ [dst_pts['x'][i], dst_pts['y'][i]] for i in N ])
  logging.debug(src_pts)
  logging.debug(dst_pts)
  return src_pts, dst_pts


if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('-1', '--image_path1', required=True)
  parser.add_argument('-2', '--image_path2', required=True)
  parser.add_argument('--matches_path', required=True)
  parser.add_argument('--winsize1', type=int, default=500)
  parser.add_argument('--winsize2', type=int, default=500)
  parser.add_argument('--name1', default='frame')
  parser.add_argument('--name2', default='map')
  parser.add_argument('--logging', type=int, default=20, choices=[10,20,30,40])
  args = parser.parse_args()
  
  logging.basicConfig(level=args.logging, format='%(levelname)s: %(message)s')

  assert op.exists(image_path1), image_path1
  assert op.exists(image_path2), image_path2
  img1 = imread(image_path1)
  img2 = imread(image_path2)
  assert img1 is not None
  assert img2 is not None

  labelMatches (img1, img2, args.matches_path,
      winsize1=args.winsize1, winsize2=args.winsize2,
      name1=args.name1, name2=args.name2)
