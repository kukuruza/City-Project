import os, sys, os.path as op
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import abc
import logging
import shutil
import glob
import json
import sqlite3
import numpy as np
import cv2
import copy
from tqdm import trange, tqdm
from skimage import color
from scipy.misc import imresize
from pprint import pprint
from datetime    import datetime  # to print creation timestamp in readme.txt
from learning.helperDb    import carField, doesTableExist
from learning.dbUtilities import bbox2roi, expandRoiFloat, mask2bbox
from learning.helperSetup import setParamUnlessThere, assertParamIsThere, atcity
from learning.helperImg   import ReaderVideo, SimpleWriter
from learning.helperKeys  import KeyReaderUser



def dbReplaceCarsWithNpz (c, in_npz_file, out_video_file, params={}):
  logging.info('=== ReplaceCarsWithNpz ===')
  setParamUnlessThere (params, 'num', 1000000000)
  setParamUnlessThere (params, 'score_threshold', 1.0)
  setParamUnlessThere (params, 'replace_fraction', 1.0)
  setParamUnlessThere (params, 'car_constraint', '1')
  setParamUnlessThere (params, 'image_constraint', '1')
  pprint(params)

  logging.info('loading...')
  a = np.load(atcity(in_npz_file))
  patches = a['cars']
  carids  = a['carids']
  logging.info('finished loading')
  carid2npz  = dict([(x, i) for i,x in enumerate(carids)])
  logging.info('found %d cars in npz' % len(carids))

  # supports output to one video only
  reader = ReaderVideo()
  writer = SimpleWriter(vimagefile=out_video_file, params={'unsafe': True})

  c.execute('SELECT imagefile FROM images WHERE %s' % params['image_constraint'])
  imagefiles = c.fetchall()
  for imagefile, in tqdm(imagefiles[:params['num']]):
    img = reader.imread(imagefile)

    s = 'SELECT * FROM cars WHERE imagefile=\"%s\" AND score > %d AND %s' % \
               (imagefile, params['score_threshold'], params['car_constraint'])
    logging.debug(s)
    c.execute(s)
    car_entries = c.fetchall()
    logging.debug('found %d cars in imagefile %s' % (len(car_entries), imagefile))

    # replace only a random percentage
    np.random.shuffle(car_entries)
    car_entries = car_entries[:int(len(car_entries)*params['replace_fraction'])]

    for car_entry in car_entries:
      logging.debug('found %d cars in imagefile %s' % (len(car_entries), imagefile))
      roi = carField(car_entry, 'roi')
      carid = carField(car_entry, 'id')
      width = carField(car_entry, 'width')
      height = carField(car_entry, 'height')
      logging.debug('carid %s has roi %s' % (carid, str(roi)))

      if int(carid) not in carid2npz:
        logging.warning('car %s not in npz file' % carid)
        continue

      patch = patches[carid2npz[int(carid)]]
      assert len(patch.shape) == 3 and patch.shape[2] == 3

      patch = imresize(patch, (height, width))
      img[roi[0]:roi[2]+1, roi[1]:roi[3]+1, :] = patch
      #img[roi[0]:roi[2]+1, roi[1]:roi[3]+1, :] = 0

    new_imagefile = writer.imwrite(img)
    logging.debug('updating imagefile %s to %s' % (imagefile, new_imagefile))
    c.execute('UPDATE images SET imagefile=? WHERE imagefile=?', (new_imagefile, imagefile))
    for car_entry in car_entries:
      c.execute('UPDATE cars SET imagefile=? WHERE imagefile=?', (new_imagefile, imagefile))




def dbExportCarsNpz (c, out_npz_file, params={}):
  logging.info('=== dbExportCarsNpz ===')
  setParamUnlessThere (params, 'grayscale', False)
  assertParamIsThere (params, 'width')
  assertParamIsThere (params, 'height')

  c.execute('SELECT * FROM cars')
  cars = c.fetchall()

  reader = ReaderVideo()
  if params['grayscale']:
    arr = np.zeros((len(cars),params['height'],params['width']), np.uint8)
  else:
    arr = np.zeros((len(cars),params['height'],params['width'],3), np.uint8)
  logging.info ('init array of shape %s' % str(arr.shape))

  # via list for efficient appending. Cant pre-allocate 
  carids = []
  patches = []

  for icar,car in enumerate(cars):
    carid = carField(car, 'id')
    imagefile = carField(car, 'imagefile')
    roi = carField(car, 'roi')
    logging.info ('processing %d patch from imagefile %s' % (icar, imagefile))
    img = reader.imread(imagefile)
    patch = img[roi[0]:roi[2], roi[1]:roi[3], :]
    if params['grayscale']:
      patch = color.rgb2gray(patch)
    try:
      patch = imresize(patch, (params['height'], params['width']))
      patches.append(patch)
      carids.append(carid)
    except ValueError:
      logging.error('car %d from %s is bad' % (carid, imagefile))
    
  patches = np.array(patches)
  carids  = np.array(carids)
  np.savez(atcity(out_npz_file), cars=patches, carids=carids)





