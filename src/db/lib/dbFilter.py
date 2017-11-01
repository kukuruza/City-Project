import os, sys, os.path as op
import numpy as np
import cv2
import logging
import json
from tqdm import tqdm
from helperDb import deleteCars, deleteCar, carField, imageField, doesTableExist
from annotations.terms import TermTree
from dbUtilities import drawRoi, bbox2roi
from helperSetup import atcity
from helperKeys import KeyReaderUser
from helperImg import ReaderVideo


def add_parsers(subparsers):
  filterByBorderParser(subparsers)
  filterByIntersectionParser(subparsers)
  filterUnknownNamesParser(subparsers)
  filterCustomParser(subparsers)
  deleteEmptyImagesParser(subparsers)
  thresholdScoreParser(subparsers)


def isPolygonAtBorder (xs, ys, width, height, border_thresh_perc):
  border_thresh = (height + width) / 2 * border_thresh_perc
  dist_to_border = min (xs, [width - x for x in xs], ys, [height - y for y in ys])
  num_too_close = sum([x < border_thresh for x in dist_to_border])
  return num_too_close >= 2

def isRoiAtBorder (roi, width, height, border_thresh_perc):
  border_thresh = (height + width) / 2 * border_thresh_perc
  logging.debug('border_thresh: %f' % border_thresh)
  return min (roi[0], roi[1], height+1 - roi[2], width+1 - roi[3]) < border_thresh



def filterByBorderParser(subparsers):
  parser = subparsers.add_parser('filterByBorder',
    description='Delete bboxes closer than "border_thresh_perc" from border.')
  parser.set_defaults(func=filterByBorder)
  parser.add_argument('--border_thresh_perc', default=0.03)
  parser.add_argument('--display_border', action='store_true')

def filterByBorder (c, args):
  logging.info ('==== filterByBorder ====')
  has_polygons = doesTableExist(c, 'polygons')
  has_matches = doesTableExist(c, 'matches')

  if args.display_border:
    key = 0
    image_reader = ReaderVideo()
    key_reader = KeyReaderUser()

  c.execute('SELECT imagefile FROM images')
  for (imagefile,) in tqdm(c.fetchall()):

    if args.display_border and key != 27:
      display = image_reader.imread(imagefile)

    c.execute('SELECT width,height FROM images WHERE imagefile=?', (imagefile,))
    (imwidth, imheight) = c.fetchone()

    c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
    car_entries = c.fetchall()
    logging.debug('%d cars found for %s' % (len(car_entries), imagefile))

    for car_entry in car_entries:
      car_id = carField(car_entry, 'id')
      roi = bbox2roi (carField(car_entry, 'bbox'))

      if isRoiAtBorder(roi, imwidth, imheight, args.border_thresh_perc):
        logging.debug ('border roi %s' % str(roi))
        deleteCar (c, car_id, has_polygons=has_polygons, has_matches=has_matches)
        if args.display_border and key != 27:
          drawRoi (display, roi, '', (0,0,255))
      else:
        if args.display_border and key != 27:
          drawRoi (display, roi, '', (255,0,0))

    if args.display_border and key != 27:
      cv2.imshow('display_border', display)
      key = key_reader.readKey()
      if key == 27: cv2.destroyWindow('display_border')




def filterByIntersectionParser(subparsers):
  parser = subparsers.add_parser('filterByIntersection',
    description='Remove cars that have high intersection with other cars.')
  parser.set_defaults(func=filterByIntersection)
  parser.add_argument('--intersection_thresh_perc', default=0.1, type=float)
  #parser.add_argument('--expand_perc', type=float, default=0.1)
  #parser.add_argument('--target_ratio', type=float, default=0.75)  # h / w.
  #parser.add_argument('--keep_ratio', action='store_true')
  parser.add_argument('--display_intersection', type=int, default=0, choices={0,1,2})

def filterByIntersection (c, args):
  '''If 'expand_bboxes' is set to True, a car is removed if the intersection
     of its expanded box and original boxes of other cars is too high.
  '''
  logging.info ('==== filterByIntersection ====')
  has_polygons = doesTableExist(c, 'polygons')
  has_matches = doesTableExist(c, 'matches')

  if args.display_intersection:
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
      #roi1 = _expandCarBbox_(car_entry1, args)
      roi1 = carField(car_entry1, 'roi')

      area1 = (roi1[2] - roi1[0]) * (roi1[3] - roi1[1])
      if area1 == 0:
        logging.warning('A car in %s has area 0. Will delete.' % imagefile)
        good_cars[icar1] = False
        break

      for icar2, car_entry2 in enumerate(car_entries):
        if icar2 == icar1:
          continue
        roi2 = carField(car_entry2, 'roi')
        overlay_perc = _get_intesection(roi1, roi2) / float(area1)
        if overlay_perc > args.intersection_thresh_perc:
          good_cars[icar1] = False
          break

      if args.display_intersection >= 2 and key != 27:
        display = image_reader.imread(imagefile).copy()
        color = (255,0,0) if good_cars[icar1] else (0,0,255)
        drawRoi (display, roi1, '', color, thickness=2)
        for icar2, car_entry2 in enumerate(car_entries):
          if icar1 == icar2: continue
          roi2 = carField(car_entry2, 'roi')
          drawRoi (display, roi2, '', color=(255,0,0))
        cv2.imshow('display_intersection', display)
        key = key_reader.readKey()
        if key == 27: cv2.destroyWindow('display_intersection')

    if args.display_intersection and key != 27:
      display = image_reader.imread(imagefile)
      for car_entry, good_car in zip(car_entries, good_cars):
        roi = carField(car_entry, 'roi')
        color = (255,0,0) if good_car else (0,0,255)
        drawRoi (display, roi, '', color)
      cv2.imshow('display_intersection', display)
      key = key_reader.readKey()
      if key == 27: cv2.destroyWindow('display_intersection')

    for car_entry, good_car in zip(car_entries, good_cars):
      if not good_car:
        car_id = carField(car_entry, 'id')
        deleteCar(c, car_id, has_polygons=has_polygons, has_matches=has_matches)



def filterUnknownNamesParser(subparsers):
  parser = subparsers.add_parser('filterUnknownNames',
    description='Filter away car entries with unknown names.')
  parser.set_defaults(func=filterUnknownNames)

def filterUnknownNames (c, args):
  # load terms tree
  dictionary_path = atcity('src/learning/annotations/dictionary.json')
  assert op.exists(dictionary_path), dictionary_path
  json_file = open(dictionary_path);
  terms = TermTree.from_dict(json.load(json_file))
  json_file.close()

  c.execute('SELECT id,name FROM cars')
  for (carid,name) in c.fetchall():
    if terms.best_match(name) == 'object':
      c.execute('DELETE FROM cars WHERE id=?', (carid,))



def filterCustomParser(subparsers):
  parser = subparsers.add_parser('filterCustom',
    description='Delete cars not matching image_constraint and car_constraint.')
  parser.set_defaults(func=filterCustom)
  parser.add_argument('--image_constraint', default='1')
  parser.add_argument('--car_constraint', default='1')

def filterCustom (c, args):
  logging.info ('==== filterCustom ====')
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



def deleteEmptyImagesParser(subparsers):
  parser = subparsers.add_parser('deleteEmptyImages')
  parser.set_defaults(func=deleteEmptyImages)

def deleteEmptyImages(c, args):
  logging.info ('==== deleteEmptyImages ====')
  c.execute('SELECT COUNT(*) FROM images WHERE imagefile NOT IN '
            '(SELECT imagefile FROM cars)')
  num, = c.fetchone()
  logging.info('deleteEmptyImages found %d empty images' % num)
  c.execute('DELETE FROM images WHERE imagefile NOT IN '
            '(SELECT imagefile FROM cars)')



def thresholdScoreParser(subparsers):
  parser = subparsers.add_parser('thresholdScore',
    description='Delete all cars that have score less than "score_threshold".')
  parser.set_defaults(func=thresholdScore)
  parser.add_argument('--score_threshold', default=0.5)

def thresholdScore (c, args):
  logging.info ('==== thresholdScore ====')
  c.execute('SELECT id FROM cars WHERE score < ?', (args.score_threshold,))
  car_ids = c.fetchall()
  deleteCars(c, car_ids)
