import sys, os, os.path as op
import logging
import argparse
import numpy as np
import cv2
from scipy.misc import imread, imresize


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


class Window:

  def __init__(self, img, winsize=500, name='display'):
    self.name = name
    self.img = pad_to_square(img.copy())
    #
    self.imgsize = self.img.shape[0]
    self.winsize = winsize
    logging.debug('%s: imgsize: %d, winsize: %d' %
        (self.name, self.imgsize, self.winsize))
    self.zoom = self.imgsize / float(self.winsize) / 2
    self.scrollx = 0.5  # 0. to 1.
    self.scrolly = 0.5  # 0. to 1.
    #
    self.rbuttonpressed = False
    self.rpressx = None
    self.rpressy = None
    #
    self.cached_zoomed_img = None
    #
    cv2.namedWindow(self.name)
    cv2.setMouseCallback(self.name, self.mouseHandler)
    self.make_cached_zoomed_img()
    self.redraw()

  def mouseHandler(self, event, x, y, flags, params):

    # Scrolling.
    if event == cv2.EVENT_LBUTTONDOWN:
      logging.info('%s: registered mouse l. press.' % self.name)
      self.rbuttonpressed = True
      self.rpressx, self.rpressy = x, y
    if event == cv2.EVENT_LBUTTONUP:
      self.rbuttonpressed = False
      self.rpressx, self.rpressy = None, None
      logging.info('%s: released mouse l. press.' % self.name)
    elif event == cv2.EVENT_MOUSEMOVE:
      if self.rbuttonpressed:
        self.scrollx -= (x - self.rpressx) / float(self.winsize)
        self.scrolly -= (y - self.rpressy) / float(self.winsize)
        self.scrollx = clip(self.scrollx, 0., 1.)
        self.scrolly = clip(self.scrolly, 0., 1.)
        self.rpressx, self.rpressy = x, y
        #logging.debug('%s: scrollx %.2f, scrolly %.2f' %
        #    (self.name, self.scrollx, self.scrolly))
        self.redraw()

    # Zooming.
    #elif event == cv2.EVENT_MOUSEWHEEL:
    #  logging.info('%s: released wheel.' % self.name)


  def make_cached_zoomed_img(self):
    ''' Cache image at a zoom level to make scrolling faster. '''
    self.cached_zoomed_img = imresize(self.img, 1. / self.zoom)

  def get_offsets(self):
    ''' Get win offsets based on zoom and scrolls '''
    assert self.cached_zoomed_img is not None
    cropsize = self.cached_zoomed_img.shape[0]
    maxoffset = cropsize - self.winsize
    logging.debug ('%s: zoom: %.1f, cropsize: %d, maxoffset: %d' %
        (self.name, self.zoom, cropsize, maxoffset))
    offsetx = int(self.scrollx * maxoffset)
    offsety = int(self.scrolly * maxoffset)
    assert offsetx >= 0 and offsetx <= self.winsize, offsetx
    assert offsety >= 0 and offsety <= self.winsize, offsety
    return offsetx, offsety
    
  def redraw(self):
    offsetx, offsety = self.get_offsets()
    crop = self.cached_zoomed_img.copy()
    crop = crop[offsety : offsety + self.winsize,
                offsetx : offsetx + self.winsize, :]
    crop = crop[:,:,::-1]  # cv2 expects image as BGR not RGB.
    cv2.imshow(self.name, crop)

  def image_to_window_coords(self, x, y):
    offsetx, offsety = self.get_offsets()
    return (x / self.zoom - offsetx,
            y / self.zoom - offsety)

  def window_to_image_coords(self, x, y):
    offsetx, offsety = self.get_offsets()
    return ((x + offsetx) * self.zoom,
            (y + offsety) * self.zoom)



if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('--image_path', required=True)
  parser.add_argument('--winsize', type=int, default=500)
  parser.add_argument('--logging', type=int, default=20, choices=[10,20,30,40])
  args = parser.parse_args()
  
  logging.basicConfig(level=args.logging, format='%(levelname)s: %(message)s')

  window = Window(imread(args.image_path), args.winsize)
  window.redraw()
  cv2.waitKey(-1)
  

