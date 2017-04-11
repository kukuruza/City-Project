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
import re
import sqlite3
from tqdm import trange, tqdm
from learning.helperDb import createTablePolygons, createDb
from learning.helperDb import parseIdatafaTimeString, makeTimeString
from learning.dbUtilities import *
from learning.helperSetup import setParamUnlessThere, atcity
from learning.labelme.parser import FrameParser
from learning.helperImg   import ReaderVideo, getVideoLength
from learning.dataset2imagery import exportVideoWBoxes


    
def _getRoi (annotation, was_scaled):
  pt = annotation.find('bndbox')
  xmin = int(pt.find('xmin').text) / was_scaled
  xmax = int(pt.find('xmax').text) / was_scaled - 1
  ymin = int(pt.find('ymin').text) / was_scaled
  ymax = int(pt.find('ymax').text) / was_scaled - 1
  roi = [ymin, xmin, ymax, xmax]
  roi = [int(x) for x in roi]
  return roi


def _vehicleType (text):
  ''' translate Shanghang's types to Evgeny's '''
  if text == '1':  return 'taxi'
  if text == '2':  return 'sedan'  # 'black sedan'
  if text == '3':  return 'sedan'
  if text == '4':  return 'truck'  # 'little truck'
  if text == '5':  return 'truck'  # 'middle truck'
  if text == '6':  return 'truck'  # 'big truck'
  if text == '7':  return 'van'
  if text == '8':  return 'bus'    # 'middle bus'
  if text == '9':  return 'bus'    # 'big bus'
  if text == '10': return 'object' # 'other'
  logging.warning ('type is not 1-9: %s' % text)
  return 'object'


def _processFrame (c, imagefile, annotation_path, params):

  # get paths and names
  logging.debug ('annotation_path: %s' % annotation_path)

  text = open(annotation_path, 'r').read()
  parser = ET.XMLParser(ns_clean=True, recover=True)
  tree = ET.parse(StringIO(text), parser)

  # do not check consistency of <video> or <frame> because Idatafa fucks it up

  # get dimensions from xml (for some reason it was rescaled)
  width  = int(tree.getroot().find('width').text)
  height = int(tree.getroot().find('height').text)
  sz = (height,width)

  # get time
  timestr = tree.getroot().find('time').text
  time = parseIdatafaTimeString(timestr)
  timestr = makeTimeString(time)

  # write image entry to db
  image_entry = (imagefile,width,height,timestr)
  s = 'images(imagefile,width,height,time)'
  c.execute('INSERT INTO %s VALUES (?,?,?,?);' % s, image_entry)

  # read only once per image
  if params['debug_show']: 
    img = params['image_reader'].imread(imagefile)

  objects = tree.getroot().findall('vehicle')
  for object_ in objects:

    # find the name of object. Filter all generic objects
    name = _vehicleType(object_.find('type').text)
    name = params['parser'].parse(name)

    # get all the points
    roi = _getRoi (object_, was_scaled=1.)

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

  logging.debug('found %d objects' % len(objects))
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



def parseIdatafaFolder (in_video_file, out_db_file, params={}):
  ''' Make a db from a standard Shanghang directory organization '''

  logging.info ('==== parseIdatafaFolder ====')
  setParamUnlessThere (params, 'debug_show', False)
  setParamUnlessThere (params, 'image_reader',   ReaderVideo())
  setParamUnlessThere (params, 'bboxes_video', False)
  params['parser'] = FrameParser()

  # create a dir for db, if necessary
  out_db_dir = op.dirname(atcity(out_db_file))
  logging.info ('out_db_dir: %s' % out_db_dir)
  if not op.exists(out_db_dir): 
    os.makedirs (out_db_dir)

  # create db
  if op.exists(out_db_file): 
    os.remove(out_db_file)
  conn = sqlite3.connect(atcity(out_db_file))
  createDb(conn)
  c = conn.cursor()
  createTablePolygons(c)

  # get all the annotations
  xmldir = op.splitext(in_video_file)[0]
  xmlpaths = sorted(glob(atcity(op.join(xmldir, '*.xml'))))
  # filename should be exactly 6 digits: XXXXXX.xml
  xmlpaths = filter(lambda x: re.compile('.*\/\d{6}.xml$').match(x), xmlpaths)
  #xmlpaths = [x for x in xmlpaths if re.compile('.*\/\d{6}.xml$').match(x)]
  logging.info ('found %d annotation files' % len(xmlpaths))

  # verify that the video covers the number of xml
  video_length = getVideoLength(in_video_file)
  if video_length < len(xmlpaths):
    logging.error('too many xml: %d < %d' % (video_length, len(xmlpaths)))
    xmlpaths = xmlpaths[:video_length]
    logging.error('dropped xmls after %s' % xmlpaths[-1])

  for i, xmlpath in enumerate(tqdm(xmlpaths)):
    xmlname = op.basename(op.splitext(xmlpath)[0])
    assert xmlname == '%06d' % (i+1), xmlname
    imagename = '%06d' % i
    imagefile = op.join(op.splitext(in_video_file)[0], imagename)
    imagefile = op.relpath(imagefile, os.getenv('CITY_PATH'))
    logging.debug('parsing xml_path: %s (imagename %s)' % (xmlpath, imagename))
    _processFrame (c, imagefile, xmlpath, params)

  # export video with bboxes
  if params['bboxes_video']:
    out_videofile = '%s-bboxes-parsed.avi' % op.splitext(in_video_file)[0]
    exportVideoWBoxes (c, out_videofile, params={'unsafe': True})

  conn.commit()
  conn.close()
