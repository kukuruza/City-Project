import os, sys, os.path as op
import numpy as np
import cv2
#import xml.etree.ElementTree as ET
from lxml import etree as ET
from StringIO import StringIO
import collections
import logging
from glob import glob
import shutil
import sqlite3
from learning.helperDb import createTablePolygons
from learning.dbUtilities import *
from learning.helperSetup import setParamUnlessThere, atcity
from learning.labelme.parser import FrameParser
from learning.helperImg   import ReaderVideo


    
def _getRoi (annotation, was_scaled):
  pt = annotation.find('bndbox')
  xmin = int(pt.find('xmin').text) / was_scaled
  xmax = int(pt.find('xmax').text) / was_scaled
  ymin = int(pt.find('ymin').text) / was_scaled
  ymax = int(pt.find('ymax').text) / was_scaled
  roi = [ymin, xmin, ymax, xmax]
  roi = [int(x) for x in roi]
  return roi


def _vehicleType (text):
  if text == '1': return 'taxi'
  if text == '2': return 'black sedan'
  if text == '3': return 'sedan'
  if text == '4': return 'little truck'
  if text == '5': return 'middle truck'
  if text == '6': return 'big truck'
  if text == '7': return 'van'
  if text == '8': return 'middle bus'
  if text == '9': return 'big bus'
  logging.warning ('type is not 1-9: %s' % text)
  return 'object'


def _processFrame (c, imagefile, annotation_path, params):

  # get paths and names
  imagename = op.basename(imagefile)
  logging.debug ('annotation_file: %s' % annotation_path)

  text = open(annotation_path, 'r').read()
  parser = ET.XMLParser(ns_clean=True, recover=True)
  tree = ET.parse(StringIO(text), parser)
  #tree = ET.parse(annotation_path, recover=True)

  # get dimensions from db
  c.execute('SELECT height,width FROM images WHERE imagefile=?', (imagefile,))
  sz = (height,width) = c.fetchone()

  # get dimensions from xml (for some reason it was rescaled)
  widthxml = int(tree.getroot().find('width').text)
  was_scaled = widthxml / float(width)


  if params['debug_show']:
    img = params['image_reader'].imread(imagefile)

  for object_ in tree.getroot().findall('vehicle'):

    # find the name of object. Filter all generic objects
    name = _vehicleType(object_.find('type').text)
    name = params['parser'].parse(name)

    # get all the points
    roi = _getRoi (object_, was_scaled)

    # validate roi
    if roi[0] < 0 or roi[1] < 0 or roi[2] >= sz[0] or roi[3] >= sz[1]:
      logging.warning ('roi %s out of borders: %s' % (str(roi), str(sz)))
    roi[0] = max(roi[0], 0)
    roi[1] = max(roi[1], 0)
    roi[2] = min(roi[2], sz[0]-1)
    roi[3] = min(roi[3], sz[1]-1)

    # make an entry for database
    bbox = roi2bbox (roi)
    car_entry = (imagefile, name, bbox[0], bbox[1], bbox[2], bbox[3])

    # write to db
    s = 'cars(imagefile,name,x1,y1,width,height)'
    c.execute('INSERT INTO %s VALUES (?,?,?,?,?,?);' % s, car_entry)

    carid = c.lastrowid
    xs = [roi[1], roi[3], roi[3], roi[1]]
    ys = [roi[0], roi[0], roi[2], roi[2]]
    for i in range(len(xs)):
      polygon = (carid, xs[i], ys[i])
      c.execute('INSERT INTO polygons(carid,x,y) VALUES (?,?,?);', polygon)

    if params['debug_show']: 
      drawRoi (img, roi, name, (0,0,255))

  if params['debug_show']: 
    cv2.imshow('debug_show', img)
    key = cv2.waitKey(-1)
    if key == 27: 
      params['debug_show'] = False
      cv2.destroyAllWindows()



def folder2frames (c, annotations_dir, params):
  ''' Process xml annotations of idatafa into db '''

  logging.info ('==== folder2frames ====')
  setParamUnlessThere (params, 'debug_show', False)
  setParamUnlessThere (params, 'image_reader',   ReaderVideo())
  params['parser'] = FrameParser()

  # list input annotations names
  assert op.exists(atcity(annotations_dir)), annotations_dir
  annotation_paths = sorted(glob(atcity('%s/*.xml' % annotations_dir)))

  createTablePolygons(c)
  c.execute('UPDATE images SET maskfile=NULL')

  c.execute('SELECT imagefile FROM images')
  imagefiles = c.fetchall()

  for i,(imagefile,) in enumerate(imagefiles):

    annotation_path = annotation_paths[i]
    logging.debug ('processing imagefile: %s' % imagefile)
    _processFrame (c, imagefile, annotation_path, params)

