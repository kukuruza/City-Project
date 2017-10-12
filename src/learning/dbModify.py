import os, sys, os.path as op
import argparse
from math import ceil
import numpy as np
import cv2
import logging
import sqlite3
import json
import random
from tqdm import trange, tqdm
import dbUtilities
from helperDb          import createDb, deleteCar, carField, imageField, deleteCars
from helperDb          import doesTableExist, createTablePolygons
from dbUtilities       import bbox2roi, roi2bbox, bottomCenter, drawRoi
from annotations.terms import TermTree
from helperSetup       import setParamUnlessThere, assertParamIsThere, atcity, ArgumentParser
from helperKeys        import KeyReaderUser
from helperImg         import ReaderVideo, ProcessorVideo, SimpleWriter


def isPolygonAtBorder (xs, ys, width, height, border_thresh_perc):
  border_thresh = (height + width) / 2 * border_thresh_perc
  dist_to_border = min (xs, [width - x for x in xs], ys, [height - y for y in ys])
  num_too_close = sum([x < border_thresh for x in dist_to_border])
  return num_too_close >= 2


def isRoiAtBorder (roi, width, height, border_thresh_perc):
  border_thresh = (height + width) / 2 * border_thresh_perc
  logging.debug('border_thresh: %f' % border_thresh)
  return min (roi[0], roi[1], height+1 - roi[2], width+1 - roi[3]) < border_thresh


def _expandCarBbox_ (car_entry, args):
  carid = carField(car_entry, 'id')
  roi = bbox2roi (carField(car_entry, 'bbox'))
  if args.keep_ratio:
    roi = dbUtilities.expandRoiToRatio(roi, args.expand_perc, args.target_ratio)
  else:
    roi = dbUtilities.expandRoiFloat(roi, (args.expand_perc, args.expand_perc))
  return roi


def _clusterBboxes_ (c, imagefile, params):
  assertParamIsThere (params, 'terms')

  c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
  car_entries = c.fetchall()
  logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

  # collect rois
  rois = []
  names = []
  #scores = []
  for car_entry in car_entries:
      roi = bbox2roi (carField(car_entry, 'bbox'))
      name = carField(car_entry, 'name')
      if name is None: name = 'vehicle'
      #score = carField(car_entry, 'score')
      rois.append (roi)
      names.append (name)
      #scores.append (score)

  # cluster rois
  #params['scores'] = scores
  (rois_clustered, clusters, scores) = dbUtilities.hierarchicalClusterRoi (rois, params)

  names_clustered = []
  for cluster in list(set(clusters)):
      names_in_cluster = [x for i, x in enumerate(names) if clusters[i] == cluster]
      # try to be as specific about the name as possible
      #for i in range(1, len(names_in_cluster)):
      #    common_root = params['terms'].get_common_root(names_in_cluster[i], names_in_cluster[i-1])
      # Start with two clusters
      name = names_in_cluster[0]
      if len(names_in_cluster) > 1:
          common_root = params['terms'].get_common_root(names_in_cluster[0], names_in_cluster[1])
          if names_in_cluster[0] == common_root:
              # names_in_cluster[1] is more specific
              name = names_in_cluster[1]
          elif names_in_cluster[1] == common_root:
              # names_in_cluster[0] is more specific
              name = names_in_cluster[0]
          else:
              # they are not in the same branch
              name = common_root
          # upgrade to the 'known' name
          name = params['terms'].best_match(name)
          logging.info ('chose "%s" from names "%s"' % (name, ','.join(names_in_cluster)))
      names_clustered.append(name)

  # draw roi on the 'display' image
  if params['debug']:
      display = params['image_processor'].imread(imagefile)
      for roi in rois:           drawRoi (display, roi, '', (0,0,255))
      for roi in rois_clustered: drawRoi (display, roi, '', (255,0,0))
      cv2.imshow('debug', display)
      if params['key_reader'].readKey() == 27:
          cv2.destroyWindow('debug')
          params['debug'] = False

  # update db
  for car_entry in car_entries:
      deleteCar (c, carField(car_entry, 'id'))
  for i in range(len(rois_clustered)):
      roi = rois_clustered[i]
      name = names_clustered[i]
      score = scores[i]
      bbox = roi2bbox(roi)
      entry = (imagefile, name, bbox[0], bbox[1], bbox[2], bbox[3], score)
      c.execute('''INSERT INTO cars(imagefile,name,x1,y1,width,height,score) 
                   VALUES (?,?,?,?,?,?,?);''', entry)


def filterByBorder (c, argv=[]):
  '''Zero 'score' of bboxes that is closer than 'border_thresh_perc' from border
  '''
  logging.info ('==== filterByBorder ====')
  parser = argparse.ArgumentParser()
  parser.add_argument('--border_thresh_perc', default=0.03)
  parser.add_argument('--debug', action='store_true')
  args, _ = parser.parse_known_args(argv)

  if args.debug:
    key = 0
    image_reader = ReaderVideo()
    key_reader = KeyReaderUser()

  c.execute('SELECT imagefile FROM images')
  for (imagefile,) in tqdm(c.fetchall()):

    if args.debug and key != 27:
      display = image_reader.imread(imagefile)

    c.execute('SELECT width,height FROM images WHERE imagefile=?', (imagefile,))
    (imwidth, imheight) = c.fetchone()

    c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
    car_entries = c.fetchall()
    logging.debug('%d cars found for %s' % (len(car_entries), imagefile))

    for car_entry in car_entries:
      carid = carField(car_entry, 'id')
      roi = bbox2roi (carField(car_entry, 'bbox'))

      if isRoiAtBorder(roi, imwidth, imheight, args.border_thresh_perc):
        logging.debug ('border roi %s' % str(roi))
        c.execute('UPDATE cars SET score=0 WHERE id=?', (carid,))
        if args.debug and key != 27:
          drawRoi (display, roi, '', (0,0,255))
      else:
        if args.debug and key != 27:
          drawRoi (display, roi, '', (255,0,0))

    if args.debug and key != 27:
      cv2.imshow('debug', display)
      key = key_reader.readKey()
      if key == 27: cv2.destroyWindow('debug')


def filterByIntersection (c, argv=[]):
  ''' Remove cars that have high intersection with other cars.
  If 'expand_bboxes' is set to True, a car is removed if the intersection
    of its expanded box and original boxes of other cars is too high.
  '''

  logging.info ('==== filterByIntersection ====')
  parser = argparse.ArgumentParser()
  parser.add_argument('--intersection_thresh_perc', default=0.1, type=float)
  parser.add_argument('--expand_perc', type=float, default=0.1)
  parser.add_argument('--target_ratio', type=float, default=0.75)  # h / w.
  parser.add_argument('--keep_ratio', action='store_true')
  parser.add_argument('--debug', action='store_true')
  parser.add_argument('--debug2', action='store_true')
  args, _ = parser.parse_known_args(argv)

  if args.debug:
    key = 0
    image_reader = ReaderVideo()
    key_reader = KeyReaderUser()

  def _get_intesection(rioi1, roi2):
    dy = min(roi1[2], roi2[2]) - max(roi1[0], roi2[0])
    dx = min(roi1[3], roi2[3]) - max(roi1[1], roi2[1])
    if dy <= 0 or dx <= 0: return 0
    return dy * dx

  c.execute('SELECT imagefile FROM images')
  for (imagefile,) in tqdm(c.fetchall()):

    c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
    car_entries = c.fetchall()
    logging.debug('%d cars found for %s' % (len(car_entries), imagefile))

    good_cars = np.ones(shape=len(car_entries), dtype=bool)
    for icar1, car_entry1 in enumerate(car_entries):
      roi1 = _expandCarBbox_(car_entry1, args)

      area1 = (roi1[2] - roi1[0]) * (roi1[3] - roi1[1])
      if area1 == 0:
        logging.warning('A car in %s has area 0. Will delete.' % imagefile)
        good_cars[icar1] = False
        break

      for icar2, car_entry2 in enumerate(car_entries):
        if icar2 == icar1:
          continue
        roi2 = bbox2roi (carField(car_entry2, 'bbox'))
        overlay_perc = _get_intesection(roi1, roi2) / float(area1)
        if overlay_perc > args.intersection_thresh_perc:
          good_cars[icar1] = False
          break

      if args.debug2 and key != 27:
        display = image_reader.imread(imagefile).copy()
        color = (255,0,0) if good_cars[icar1] else (0,0,255)
        drawRoi (display, roi1, '', color, thickness=2)
        for icar2, car_entry2 in enumerate(car_entries):
          if icar1 == icar2: continue
          roi2 = bbox2roi (carField(car_entry2, 'bbox'))
          drawRoi (display, roi2, '', color=(255,0,0))
        cv2.imshow('debug', display)
        key = key_reader.readKey()
        if key == 27: cv2.destroyWindow('debug')

    if args.debug and key != 27:
      display = image_reader.imread(imagefile)
      for car_entry, good_car in zip(car_entries, good_cars):
        roi = bbox2roi (carField(car_entry, 'bbox'))
        color = (255,0,0) if good_car else (0,0,255)
        drawRoi (display, roi, '', color)
      cv2.imshow('debug', display)
      key = key_reader.readKey()
      if key == 27: cv2.destroyWindow('debug')

    for car_entry, good_car in zip(car_entries, good_cars):
      if not good_car:
        deleteCar(c, carField(car_entry, 'id'))



def filterUnknownNames (c):
  ''' filter away car entries with unknown names '''
  
  # load terms tree
  dictionary_path = op.join(os.getenv('CITY_PATH'), 'src/learning/annotations/dictionary.json')
  json_file = open(dictionary_path);
  terms = TermTree.from_dict(json.load(json_file))
  json_file.close()

  c.execute('SELECT id,name FROM cars')
  for (carid,name) in c.fetchall():
      if terms.best_match(name) == 'object':
          c.execute('DELETE FROM cars WHERE id=?', (carid,))


def filterCustom (c, argv=[]):
  ''' Assign zero score to entries not matching image_constraint and car_constraint. '''

  logging.info ('==== filterCustom ====')
  parser = argparse.ArgumentParser()
  parser.add_argument('--image_constraint', default='1')
  parser.add_argument('--car_constraint', default='1')
  args, _ = parser.parse_known_args(argv)

  s = 'DELETE FROM images WHERE NOT (%s)' % args.image_constraint
  logging.info('command to delete images: %s' % s)
  c.execute(s)
  s = '''SELECT id FROM cars WHERE NOT (%s) OR imagefile NOT IN 
         (SELECT imagefile FROM images WHERE (%s));''' % (
          args.car_constraint, args.image_constraint)
  logging.info('command to delete cars: %s' % s)
  c.execute(s)
  car_ids = c.fetchall()
  logging.info ('Will delete %d cars.' % len(car_ids))
  if args.car_constraint is not '1':  # Skip expensive operation.
    deleteCars(c, car_ids)


def deleteEmptyImages (c):
  c.execute('SELECT COUNT(*) FROM images WHERE imagefile NOT IN '
            '(SELECT imagefile FROM cars)')
  num, = c.fetchone()
  logging.info('deleteEmptyImages found %d empty images' % num)
  c.execute('DELETE FROM images WHERE imagefile NOT IN '
            '(SELECT imagefile FROM cars)')


def filter(c, argv=[]):
  parser = ArgumentParser('filter')
  parser.add_argument('--filter_by_border', action='store_true')
  parser.add_argument('--delete_empty_images', action='store_true')
  parser.add_argument('--filter_by_intersection', action='store_true')
  args, _ = parser.parse_known_args(argv)

  if args.delete_empty_images:
    deleteEmptyImages (c)
  if args.filter_by_intersection:
    filterByIntersection (c, argv)
  filterCustom (c, argv)
  if args.filter_by_border:
    filterByBorder (c, argv)
    thresholdScore (c)

  c.execute('SELECT COUNT(*) FROM cars')
  print ('After filtering %d cars left' % c.fetchone()[0])


def thresholdScore (c, argv=[]):
  ''' Delete all cars that have score less than 'score_threshold'. '''

  logging.info ('==== thresholdScore ====')
  parser = argparse.ArgumentParser()
  parser.add_argument('--score_threshold', default=0.5)
  args, _ = parser.parse_known_args(argv)
  
  c.execute('SELECT id FROM cars WHERE score < ?', (args.score_threshold,))
  car_ids = c.fetchall()

  has_polygons = doesTableExist(c, 'polygons')
  has_matches = doesTableExist(c, 'matches')
  deleteCars(c, car_ids, has_polygons=has_polygons, has_matches=has_matches)


def expandBboxes (c, argv):
  '''Expand bbox in every direction.
  If 'keep_ratio' flag is set, the smaller of width and height will be expanded more
  '''
  logging.info ('==== expandBboxes ====')
  parser = argparse.ArgumentParser()
  parser.add_argument('--expand_perc', type=float, default=0.0)
  parser.add_argument('--target_ratio', type=float, default=1.)  # h / w.
  parser.add_argument('--keep_ratio', action='store_true')
  parser.add_argument('--debug', action='store_true')
  args, _ = parser.parse_known_args()

  if args.debug:
    key = 0
    key_reader = KeyReaderUser()
    image_reader = ReaderVideo()

  c.execute('SELECT imagefile FROM images')
  image_entries = c.fetchall()

  for (imagefile,) in image_entries:

    c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
    car_entries = c.fetchall()
    logging.debug('%d cars found for %s' % (len(car_entries), imagefile))

    if args.debug and key != 27:
      oldroi = bbox2roi (carField(car_entry, 'bbox'))

    for car_entry in car_entries:
      carid = carField(car_entry, 'id')
      roi = _expandCarBbox_(car_entry, args)
      s = 'x1=?, y1=?, width=?, height=?'
      c.execute('UPDATE cars SET %s WHERE id=?' % s, tuple(roi2bbox(roi) + [carid]))

    # draw roi on the 'display' image
    if args.debug and key != 27:
      display = image_reader.imread(imagefile)
      drawRoi (display, oldroi, '', (0,0,255))
      drawRoi (display, roi, '', (255,0,0))
      cv2.imshow('debug', display)
      key = key_reader.readKey()
      if key == 27:
        cv2.destroyWindow('debug')


def clusterBboxes (c, params = {}):
  '''
  Combine close bboxes into one, based on intersection/union ratio via hierarchical clustering
  TODO: implement score-weighted clustering
  '''
  logging.info ('==== clusterBboxes ====')
  setParamUnlessThere (params, 'cluster_threshold', 0.2)
  setParamUnlessThere (params, 'debug',             False)
  setParamUnlessThere (params, 'key_reader',        KeyReaderUser())
  setParamUnlessThere (params, 'image_processor',   ReaderVideo())

  # load terms tree
  dictionary_path = op.join(os.getenv('CITY_PATH'), 'src/learning/annotations/dictionary.json')
  json_file = open(dictionary_path);
  terms = TermTree.from_dict(json.load(json_file))
  json_file.close()
  params['terms'] = terms

  c.execute('SELECT imagefile FROM images')
  image_entries = c.fetchall()

  for (imagefile,) in image_entries:
      _clusterBboxes_ (c, imagefile, params)



def assignOrientations (c, params):
  '''
  assign 'yaw' and 'pitch' angles to each car based on provided yaw and pitch maps 
  '''
  logging.info ('==== assignOrientations ====')
  setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
  assertParamIsThere  (params, 'size_map_path')
  assertParamIsThere  (params, 'pitch_map_path')
  assertParamIsThere  (params, 'yaw_map_path')

  params['size_map_path']  = op.join(params['relpath'], params['size_map_path'])
  params['pitch_map_path'] = op.join(params['relpath'], params['pitch_map_path'])
  params['yaw_map_path']   = op.join(params['relpath'], params['yaw_map_path'])
  if not op.exists(params['size_map_path']):
      raise Exception ('size_map_path does not exist: ' + params['size_map_path'])
  if not op.exists(params['pitch_map_path']):
      raise Exception ('pitch_map_path does not exist: ' + params['pitch_map_path'])
  if not op.exists(params['yaw_map_path']):
      raise Exception ('yaw_map_path does not exist: ' + params['yaw_map_path'])
  size_map  = cv2.imread (params['size_map_path'], 0).astype(np.float32)
  pitch_map = cv2.imread (params['pitch_map_path'], 0).astype(np.float32)
  yaw_map   = cv2.imread (params['yaw_map_path'], -1).astype(np.float32)
  # in the tiff angles belong to [0, 360). Change that to [-180, 180)
  yaw_map   = np.add(-180, np.mod( np.add(180, yaw_map), 360 ) )

  c.execute('SELECT * FROM cars')
  car_entries = c.fetchall()

  for car_entry in car_entries:
      carid = carField (car_entry, 'id')
      roi = bbox2roi (carField (car_entry, 'bbox'))
      bc = bottomCenter(roi)
      if size_map[bc[0], bc[1]] > 0:
          yaw   = float(yaw_map   [bc[0], bc[1]])
          pitch = float(pitch_map [bc[0], bc[1]])
          c.execute('UPDATE cars SET yaw=?, pitch=? WHERE id=?', (yaw, pitch, carid))


def moveDir (c, params):
  logging.info ('==== moveDir ====')
  setParamUnlessThere (params, 'images_dir', None)
  setParamUnlessThere (params, 'masks_dir', None)

  if params['images_dir'] is not None:
      logging.debug ('images_dir: %s' % params['images_dir'])
      c.execute('SELECT imagefile FROM images')
      imagefiles = c.fetchall()

      for (oldfile,) in tqdm(imagefiles, desc='image_dir'):
          # op.basename (op.dirname(oldfile)), 
          newfile = op.join (params['images_dir'], op.basename (oldfile))
          c.execute('UPDATE images SET imagefile=? WHERE imagefile=?', (newfile, oldfile))
          c.execute('UPDATE cars SET imagefile=? WHERE imagefile=?', (newfile, oldfile))

  if params['masks_dir'] is not None:
      logging.debug ('masks_dir: %s' % params['masks_dir'])
      c.execute('SELECT maskfile FROM images')
      maskfiles = c.fetchall()

      for (oldfile,) in tqdm(maskfiles, desc='mask_dir'):
          # op.basename (op.dirname(oldfile)), 
          newfile = op.join (params['masks_dir'], op.basename (oldfile))
          c.execute('UPDATE images SET maskfile=? WHERE maskfile=?', (newfile, oldfile))


    
def merge (c, c_add, params = {}):
  '''
  Merge images and cars (TODO: matches) from 'c_add' to current database
  '''
  logging.info ('==== merge ====')

  # copy images
  c_add.execute('SELECT * FROM images')
  image_entries = c_add.fetchall()

  for image_entry in image_entries:
      imagefile = image_entry[0]
      # check that doesn't exist
      c.execute('SELECT count(*) FROM images WHERE imagefile=?', (imagefile,))
      (num,) = c.fetchone()
      if num > 0:
          logging.warning ('duplicate image found %s' % imagefile) 
          continue
      # insert image
      logging.info ('merge: insert imagefile: %s' % (imagefile,))
      c.execute('INSERT INTO images VALUES (?,?,?,?,?,?)', image_entry)
  
  # copy cars and polygons
  c_add.execute('SELECT * FROM cars')
  car_entries = c_add.fetchall()

  for car_entry in car_entries:

      # insert car
      carid = carField (car_entry, 'id')
      s = 'cars(imagefile,name,x1,y1,width,height,score,yaw,pitch,color)'
      c.execute('INSERT INTO %s VALUES (?,?,?,?,?,?,?,?,?,?)' % s, car_entry[1:])
      new_carid = c.lastrowid

      # insert all its polygons
      if doesTableExist(c_add, 'polygons'):
          if not doesTableExist(c, 'polygons'): 
              createTablePolygons(c)
          c_add.execute('SELECT x,y FROM polygons WHERE carid = ?', (carid,))
          polygon_entries = c_add.fetchall()
          for x,y in polygon_entries:
              s = 'polygons(carid,x,y)'
              c.execute('INSERT INTO %s VALUES (?,?,?)' % s, (new_carid,x,y))



def split (c, out_dir, db_out_names={'train': 0.5, 'test': 0.5}, randomly=True):
  ''' Split a db into several sets (randomly or sequentially).
  This function violates the principle of receiving cursors, for simplicity.
  Args: out_dir      - relative to CITY_DATA_PATH
        db_out_names - names of output db-s and their percentage;
                       if percentage sums to >1, last db-s will be underfilled.
  '''
  c.execute('SELECT imagefile FROM images')
  imagefiles = sorted(c.fetchall())
  if randomly: random.shuffle(imagefiles)

  current = 0
  for db_out_name,setfraction in db_out_names.iteritems():
    num_images_in_set = int(ceil(len(imagefiles) * setfraction))
    next = min(current + num_images_in_set, len(imagefiles))

    logging.info('writing %d images to %s' % (num_images_in_set, db_out_name))
    db_out_path = atcity(op.join(out_dir, '%s.db' % db_out_name))
    if op.exists(db_out_path): os.remove(db_out_path)
    conn = sqlite3.connect(db_out_path)
    createDb(conn)
    c_out = conn.cursor()

    for imagefile, in imagefiles[current : next]:

      # copy an entry from image table
      s = 'imagefile,width,height,src,maskfile,time'
      c.execute('SELECT %s FROM images WHERE imagefile=?' % s, (imagefile,))
      c_out.execute('INSERT INTO images(%s) VALUES (?,?,?,?,?,?)' % s, c.fetchone())

      # copy cars for that imagefile (ids are not copied)
      s = 'imagefile,name,x1,y1,width,height,score,yaw,pitch,color'
      c.execute('SELECT %s FROM cars WHERE imagefile=?' % s, (imagefile,))
      for car in c.fetchall():
        c_out.execute('INSERT INTO cars(%s) VALUES (?,?,?,?,?,?,?,?,?,?)' % s, car)

    current = next

    conn.commit()
    conn.close()

  # copying matches is not implemented (how to copy them anyway?)
  c.execute('SELECT COUNT(*) FROM matches')
  if c.fetchone()[0] > 0:
    logging.warning('matches table is not empty, they will not be copied.')



def keepFraction (c, keep_fraction=None, keep_num=None, randomly=True):
  '''Remove 1-keep_fraction Or all-keep_num images and their cars. 
  '''
  c.execute('SELECT imagefile FROM images')
  imagefiles = sorted(c.fetchall())
  if randomly: random.shuffle(imagefiles)

  if keep_fraction is not None:
    assert keep_fraction > 0 and keep_fraction <= 1
    num_to_remove = int((1 - keep_fraction) * len(imagefiles))
  elif keep_num is not None:
    assert keep_num > 0 and keep_num <= len(imagefiles)
    num_to_remove = len(imagefiles) - keep_num
  
  for imagefile, in tqdm(imagefiles[-num_to_remove:]):
    c.execute('DELETE FROM images WHERE imagefile=?', (imagefile,))
    c.execute('DELETE FROM cars   WHERE imagefile=?', (imagefile,))



def filterOneWithAnother (c, c_ref):
  '''Keep only those image _names_ in c, that exist in c_ref.
  '''
  c_ref.execute('SELECT imagefile FROM images')
  ref_imagefiles = c_ref.fetchall()
  ref_imagenames = [op.basename(x) for x, in ref_imagefiles]

  c.execute('SELECT imagefile FROM images')
  imagefiles = c.fetchall()

  del_imagefiles = [x for x, in imagefiles if op.basename(x) not in ref_imagenames]
  for del_imagefile in del_imagefiles:
    c.execute('DELETE FROM images WHERE imagefile=?', (del_imagefile,))
    c.execute('DELETE FROM cars   WHERE imagefile=?', (del_imagefile,))



def diffImagefiles (c, c_ref, params = {}):
  ''' Difference between two databases.
  Only those imagefiles which are not in c_ref are kept. 
  '''
  logging.info ('==== diffImagefiles ====')
    
  c_ref.execute('SELECT imagefile FROM images')
  imagefiles_ref = c_ref.fetchall()
   
  for imagefile, in imagefiles_ref:
    logging.debug('deleting %s' % imagefile)
    c.execute('DELETE FROM images WHERE imagefile=?', (imagefile,))
    c.execute('DELETE FROM cars   WHERE imagefile=?', (imagefile,))


# not supported because not used at the moment
def maskScores (c, params = {}):
  '''
  Apply a map (0-255) that will reduce the scores of each car accordingly (255 -> keep same)
  '''
  logging.info ('==== maskScores ====')
  assertParamIsThere (params, 'score_map_path')

  # load the map of scores and normalize it by 1/255
  score_map_path = atcity(params['score_map_path'])
  if not op.exists(score_map_path):
      raise Exception ('score_map_path does not exist: ' + score_map_path)
  score_map = cv2.imread(score_map_path, -1).astype(float);
  score_map /= 255.0

  c.execute('SELECT * FROM cars')
  car_entries = c.fetchall()

  for car_entry in car_entries:
      carid = carField (car_entry, 'id')
      bbox  = carField (car_entry, 'bbox')
      score = carField (car_entry, 'score')
      if not score: score = 1 

      center = bottomCenter(bbox2roi(bbox))
      score *= score_map[center[0], center[1]]
      c.execute('UPDATE cars SET score=? WHERE id=?', (score, carid))



# TODO: need a unit test
def polygonsToMasks (c, c_labelled=None, c_all=None, params = {}):
  '''
  Create masks and maskfile db entries from polygons table.
  Currently only supports ProcessorVideo (writes masks to video)
  '''
  logging.info ('==== polygonsToMasks ====')
  setParamUnlessThere (params, 'relpath',    os.getenv('CITY_DATA_PATH'))
  setParamUnlessThere (params, 'mask_name',  'mask-poly.avi')

  # Assume mask field is null. Deduce the out mask name from imagefile.
  #   Also send the image video to processor, so that it deduces video params.
  c_all.execute('SELECT imagefile,width,height FROM images')
  image_entries = c_all.fetchall()
  in_image_video_file = '%s.avi' % op.dirname(image_entries[0][0])
  out_mask_video_file = '%s/%s' % (op.dirname(in_image_video_file), params['mask_name'])
  logging.info ('polygonsToMasks: in_image_video_file: %s' % in_image_video_file)
  logging.info ('polygonsToMasks: out_mask_video_file: %s' % out_mask_video_file)
  processor = ProcessorVideo \
       ({'out_dataset': {in_image_video_file: out_mask_video_file} })

  # copy images and possibly masks
  for i,(imagefile,width,height) in enumerate(image_entries):
    processor.maskread (imagefile)  # processor needs to read first
    
    c_labelled.execute('SELECT COUNT(*) FROM images WHERE imagefile=?', (imagefile,))
    is_unlabelled = (c_labelled.fetchone()[0] == 0)

    if is_unlabelled:
      logging.info ('imagefile NOT labelled: %s: ' % imagefile)
      mask = np.zeros((height, width), dtype=bool)
      maskfile = processor.maskwrite (mask, imagefile)
      c.execute('UPDATE images SET maskfile=NULL WHERE imagefile=?', (imagefile,))

    else:
      logging.info ('imagefile labelled:     %s: ' % imagefile)
      mask = np.zeros((height, width), dtype=np.uint8)
      c_labelled.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
      for car_entry in c_labelled.fetchall():
        carid = carField(car_entry, 'id')
        c_labelled.execute('SELECT x,y FROM polygons WHERE carid = ?', (carid,))
        polygon_entries = c_labelled.fetchall()
        pts = [[pt[0], pt[1]] for pt in polygon_entries]
        cv2.fillConvexPoly(mask, np.asarray(pts, dtype=np.int32), 255)
        # maybe copy car entry
        if c != c_labelled:  # c == c_all
          c.execute('INSERT INTO cars VALUES (?,?,?,?,?,?,?,?,?,?,?)', car_entry)
      mask = mask > 0

      maskfile = processor.maskwrite (mask, imagefile)
      c.execute('UPDATE images SET maskfile=? WHERE imagefile=?', 
        (maskfile, imagefile))



# need a unit test
def polygonsToMasks_old (c, params = {}):
  '''
  Create masks and maskfile db entries from polygons table.
  Currently only supports ProcessorVideo (writes masks to video)
  '''
  logging.info ('==== polygonsToMasks ====')
  setParamUnlessThere (params, 'relpath',    os.getenv('CITY_DATA_PATH'))
  setParamUnlessThere (params, 'mask_name',  'mask-poly.avi')

  # Assume mask field is null. Deduce the out mask name from imagefile.
  #   Also send the image video to processor, so that it deduces video params.
  c.execute('SELECT imagefile,width,height FROM images')
  image_entries = c.fetchall()
  in_image_video_file = '%s.avi' % op.dirname(image_entries[0][0])
  out_mask_video_file = '%s/%s' % (op.dirname(in_image_video_file), params['mask_name'])
  logging.info ('polygonsToMasks: in_image_video_file: %s' % in_image_video_file)
  logging.info ('polygonsToMasks: out_mask_video_file: %s' % out_mask_video_file)
  processor = ProcessorVideo \
          ({'out_dataset': {in_image_video_file: out_mask_video_file} })

  # copy images and possibly masks
  for (imagefile,width,height) in image_entries:
    processor.maskread (imagefile)  # processor needs to read first

    mask = np.zeros((height, width), dtype=np.uint8)
    c.execute('SELECT id FROM cars WHERE imagefile=?', (imagefile,))
    for (carid,) in c.fetchall():
      c.execute('SELECT x,y FROM polygons WHERE carid = ?', (carid,))
      polygon_entries = c.fetchall()
      pts = [[pt[0], pt[1]] for pt in polygon_entries]
      cv2.fillConvexPoly(mask, np.asarray(pts, dtype=np.int32), 255)
    mask = mask > 0

    maskfile = processor.maskwrite (mask, imagefile)
    c.execute('UPDATE images SET maskfile=? WHERE imagefile=?', (maskfile, imagefile))
    logging.info ('saved mask to file: %s' % maskfile)



# TODO: need a unit test
def generateBackground (c, out_videofile, params={}):
  ''' Generate background video using mask and update imagefiles in db. '''

  logging.info ('==== polygonsToMasks ====')
  setParamUnlessThere (params, 'relpath',       os.getenv('CITY_DATA_PATH'))
  setParamUnlessThere (params, 'show_debug',    False)
  setParamUnlessThere (params, 'key_reader',    KeyReaderUser())
  setParamUnlessThere (params, 'image_reader',  ReaderVideo())
  setParamUnlessThere (params, 'dilate_radius', 2);
  setParamUnlessThere (params, 'lr',            0.2);

  video_writer = SimpleWriter(vimagefile=out_videofile)

  # structure element for dilation
  rad = params['dilate_radius']
  kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (rad, rad))

  c.execute('SELECT imagefile,maskfile FROM images')
  image_entries = c.fetchall()
  logging.info ('will process %d image entries' % len(image_entries))

  back = None

  for imagefile,maskfile in image_entries:
    img = params['image_reader'].imread(imagefile)
    mask = params['image_reader'].maskread(maskfile)

    if back is None:
      back = img

    mask = cv2.dilate(mask.astype(np.uint8)*255, kernel) > 128
    mask = np.dstack((mask, mask, mask))
    unmasked = np.invert(mask)
    lr = params['lr']
    back[unmasked] = img[unmasked] * lr + back[unmasked] * (1-lr)

    if params['show_debug']:
      cv2.imshow('debug', np.hstack((back, mask.astype(np.uint8)*255)))
      cv2.waitKey(10)
      if params['key_reader'].readKey() == 27:
        cv2.destroyWindow('debug')
        params['show_debug'] = False

    backfile = video_writer.imwrite(back)
    c.execute('UPDATE images SET imagefile=? WHERE imagefile=?', (backfile, imagefile))
    logging.info ('wrote backfile %s' % backfile)

  video_writer.close()
  c.execute('DELETE FROM cars')

