import sys, os, os.path as op
import logging
import shutil
import argparse
import numpy as np
import cv2
import simplejson as json
from scipy.misc import imread
from lib.cvScrollZoomWindow import Window


def pad_to_square(img):
  ''' Pads the right or the bottom of an image to make it square. '''
  assert img is not None
  pad = abs(img.shape[0] - img.shape[1])
  if img.shape[0] < img.shape[1]:
    img = np.pad(img, ((0,pad),(0,0),(0,0)), 'constant')
  else:
    img = np.pad(img, ((0,0),(0,pad),(0,0)), 'constant')
  return img

def clip(x, xmin, xmax):
  return max(min(x, xmax), xmin)


class MatchWindow(Window):

  def __init__(self, img, winsize=500, name='display'):
    Window.__init__(self, img, winsize, name)
    self.pointx = None
    self.poitny = None

  def mouseHandler(self, event, x, y, flags, params):
    # Call navigation handler from the base class.
    Window.mouseHandler(self, event, x, y, flags, params)

    # Select a point.
    if event == cv2.EVENT_LBUTTONDBLCLK:
      logging.info('%s: registered mouse l. double click.' % self.name)
      self.rpressx, self.rpressy = x, y




def labelMatches (image_path1, image_path2, matches_path, 
                  winsize1=500, winsize2=500, backup_matches=True):

  # If already exists, we'll load existing matches.
  # pts_pairs is a list of tuples (x_frame, y_frame, x_satellite, y_satellite)
  if op.exists(matches_path):
    if backup_matches:
      backup_path = op.splitext(matches_path)[0] + '.backup.json'
      shutil.copyfile(matches_path, backup_path)
    with open(matches_path) as f:
      matches = json.load(f)
    pts_pairs = zip(*(matches['frame']['x'], matches['frame']['y'],
                      matches['map']['x'], matches['map']['y']))
  else:
    pts_pairs = []

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
  window1 = Window(img1, args.winsize1, name=name1)
  window2 = Window(img2, args.winsize2, name=name2)

  BUTTON_ESCAPE = 27
  BUTTON_ENTER = 13
  button = -1
  while button != BUTTON_ESCAPE and button != BUTTON_ENTER:
    button = cv2.waitKey(50)

  # Save and exit.
  if button == BUTTON_ENTER:
    if len(pts_pairs) > 0:
      matches = {'frame': {'x': [], 'y': []}, 'map': {'x': [], 'y': []}}
      matches['frame']['x'], matches['frame']['y'], \
      matches['map']['x'], matches['map']['y'] = map(list, zip(*pts_pairs))
      with open(matches_path, 'w') as f:
        f.write(json.dumps(matches, sort_keys=True, indent=2))
    else:
      logging.warning('No points - will not write matches.json file.')
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
