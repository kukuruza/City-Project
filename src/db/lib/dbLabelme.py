import os, sys, os.path as op
import numpy as np
import cv2
from lxml import etree as ET
import collections
import logging
import glob
import shutil
import sqlite3
import progressbar
from .dbUtilities import overlapRatio, roi2bbox
from .helperSetup import atcity
from .helperDb import carField
from .annotations.parser import FrameParser, PairParser
from .helperImg import ReaderVideo


def add_parsers(subparsers):
  importLabelmeFramesParser(subparsers)
  importLabelmeCarsParser(subparsers)


def _pointsOfPolygon (annotation):
    pts = annotation.find('polygon').findall('pt')
    xs = []
    ys = []
    for pt in pts:
        xs.append( int(pt.find('x').text) )
        ys.append( int(pt.find('y').text) )
    return xs, ys

def _isPolygonDegenerate(xs, ys):
    assert len(xs) == len(ys), (len(xs), len(ys))
    return len(xs) == 1 or len(xs) == 2 or min(xs) == max(xs) or min(ys) == max(ys)

def _isOutOfBorders(roi, shape):
    ''' For some reason, width+1, height+1 happens. '''
    return roi[0] < 0 or roi[1] < 0 or roi[2] >= shape[0]+1 or roi[3] >= shape[1]+1


def _processFrame (c, imagefile, annotations_dir, args):

    # get paths and names
    imagename = op.basename(imagefile)
    for template in ['%s.xml', '%s..xml']:
      logging.debug('Template: %s' % template)
      annotation_name = template % op.splitext(imagename)[0]
      annotation_file = op.join(annotations_dir, annotation_name)
      logging.debug('Annotation_file: %s' % annotation_file)
      if op.exists(atcity(annotation_file)):
        break
      else:
        annotation_file = None

    # if annotation file does not exist then this imagre is not annotated
    if annotation_file is None:
        logging.debug ('This image is not annotated. Skip it.')
        return False

    logging.debug('Found annotation_file "%s" for imagefile "%s"' % 
        (annotation_file, imagefile))
    tree = ET.parse(atcity(annotation_file))

    # get dimensions
    c.execute('SELECT height,width FROM images WHERE imagefile=?', (imagefile,))
    sz = (height,width) = c.fetchone()

    if args.display:
        img = args.reader.imread(imagefile)

    for object_ in tree.getroot().findall('object'):

        # skip if it was deleted
        if object_.find('deleted').text == '1': continue

        # find the name of object. Filter all generic objects
        # name = args.parser.parse(object_.find('name').text)
        # if name == 'object':
        #     logging.info('skipped an "object"')
        #     continue
        # if name is None:
        #     logging.info('skipped a None')
        #     continue

        # get all the points
        xs, ys = _pointsOfPolygon(object_)

        # filter out degenerate polygons
        if _isPolygonDegenerate(xs, ys):
            logging.info('degenerate polygon %s,%s in %s' % (str(xs), str(ys), annotation_name))
            continue

        # make roi
        roi = [min(ys), min(xs), max(ys), max(xs)]

        # validate roi
        if _isOutOfBorders(roi, sz):
            logging.warning ('roi %s out of borders: %s' % (str(roi), str(sz)))
        roi[0] = max(roi[0], 0)
        roi[1] = max(roi[1], 0)
        roi[2] = min(roi[2], sz[0]-1)
        roi[3] = min(roi[3], sz[1]-1)
        bbox = roi2bbox (roi)

        # That car may already exist there and a polygon should be simply added to that car.
        have_merged = False
        if args.merge_cars:
            ThresholdIoU = 0.5
            c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
            existing_car_entries = c.fetchall()
            for existing_car_entry in existing_car_entries:
                existing_carid = carField(existing_car_entry, 'id')
                existing_roi = carField(existing_car_entry, 'roi')
                IoU = overlapRatio(roi, existing_roi)
                if IoU > ThresholdIoU and have_merged:
                    logging.error('Another car %d qualifies for merging.' % existing_carid)
                elif IoU > ThresholdIoU:
                    logging.info('Merging a polygon to car %d' % existing_carid)
                    have_merged = True
                    carid = existing_carid

                    c.execute('SELECT COUNT(id) FROM polygons WHERE carid=?', (existing_carid,))
                    already_has_polygons = c.fetchone()[0] > 0
                    if already_has_polygons:
                        logging.error('Merged car %d already has polygons' % existing_carid)

                    # Update name and bbox.
                    c.execute('UPDATE cars SET name=?, x1=?, y1=?, width=?, height=? WHERE id=?',
                        (name, bbox[0], bbox[1], bbox[2], bbox[3], existing_carid))

            if not have_merged:
                logging.warning('An object has no candidate to merge: %s' % car_entry)

        if not have_merged:
            car_entry = (imagefile, name, bbox[0], bbox[1], bbox[2], bbox[3])
            s = 'cars(imagefile,name,x1,y1,width,height)'
            c.execute('INSERT INTO %s VALUES (?,?,?,?,?,?);' % s, car_entry)
            carid = c.lastrowid

        for i in range(len(xs)):
            polygon = (carid, xs[i], ys[i])
            c.execute('INSERT INTO polygons(carid,x,y) VALUES (?,?,?);', polygon)

        if args.display: 
            #drawRoi (img, roi, (0,0), name, (255,255,255))
            pts = np.array([xs, ys], dtype=np.int32).transpose()
            cv2.polylines(img, [pts], True, (255,255,255))

    if args.display: 
        cv2.imshow('display', img)
        key = cv2.waitKey(-1)
        if key == 27:
            args.display = False
            cv2.destroyWindow('display')

    return True


def importLabelmeFramesParser(subparsers):
  parser = subparsers.add_parser('importLabelmeFrames',
    description='Import labelme annotations for a db.')
  parser.set_defaults(func=importLabelmeFrames)
  parser.add_argument('--in_annotations_dir', required=True,
      help='Directory with xml files.')
  parser.add_argument('--display', action='store_true')
  parser.add_argument('--merge_cars', action='store_true',
      help='Find existing cars in the database and add polygons to them.')

def importLabelmeFrames (c, args):

    logging.info ('==== importLabelmeFrames ====')
    args.parser = FrameParser()
    args.reader = ReaderVideo(args.relpath)

    c.execute('SELECT imagefile FROM images')
    imagefiles = c.fetchall()

    num_parsed = 0
    for imagefile, in imagefiles:
        logging.debug ('Processing imagefile: "%s"' % imagefile)
        if _processFrame (c, imagefile, args.in_annotations_dir, args):
            num_parsed += 1

    logging.info('Parsed %d frames.' % num_parsed)


def _processCar (c, carid, imagefile, annotations_dir, args):

    # get paths and names
    for template in ['%09d.xml', '%09d..xml']:
      logging.debug('Template: %s' % template)
      annotation_name = template % carid
      annotation_file = op.join(annotations_dir, annotation_name)
      logging.debug('Annotation_file: %s' % annotation_file)
      if op.exists(atcity(annotation_file)):
        break
      else:
        annotation_file = None

    # if annotation file does not exist then this imagre is not annotated
    if annotation_file is None:
        logging.debug ('This car is not annotated. Skip it.')
        return False

    logging.debug('Found annotation_file "%s" for carid %d in imagefile "%s"' % 
        (annotation_file, carid, imagefile))
    tree = ET.parse(atcity(annotation_file))

    objects_ = tree.getroot().findall('object')

    # remove all deleted
    objects_ = [object_ for object_ in objects_ if object_.find('deleted').text != '1']
    if len(objects_) > 1:
        logging.error('More than one object in %s' % annotation_name)
        return False
    object_ = objects_[0]

    # find the name of object.
    #name = args.parser.parse(object_.find('name').text)

    # get all the points
    xs, ys = _pointsOfPolygon(object_)

    # validate roi
    c.execute('SELECT height,width FROM images WHERE imagefile=?', (imagefile,))
    shape = (height,width) = c.fetchone()
    roi = [min(ys), min(xs), max(ys), max(xs)]
    if _isOutOfBorders(roi, shape):
        logging.warning ('roi %s out of borders: %s' % (str(roi), str(shape)))

    # Filter out degenerate polygons
    if _isPolygonDegenerate(xs, ys):
        logging.error('degenerate polygon %s,%s in %s' % (str(xs), str(ys), annotation_name))
        return False
        
    # Update polygon.
    for i in range(len(xs)):
        polygon = (carid, xs[i], ys[i])
        c.execute('INSERT INTO polygons(carid,x,y) VALUES (?,?,?);', polygon)

    if args.display:
        img = args.reader.imread(imagefile)
        pts = np.array([xs, ys], dtype=np.int32).transpose()
        cv2.polylines(img, [pts], True, (255,255,255))
        cv2.imshow('display', img)
        key = cv2.waitKey(-1)
        if key == 27:
            args.display = False
            cv2.destroyWindow('display')

    return True


def importLabelmeCarsParser(subparsers):
  parser = subparsers.add_parser('importLabelmeCars',
    description='Import labelme annotations for a db.')
  parser.set_defaults(func=importLabelmeCars)
  parser.add_argument('--in_annotations_dir', required=True,
      help='Directory with xml files.')
  parser.add_argument('--display', action='store_true')

def importLabelmeCars (c, args):

    logging.info ('==== importLabelmeCars ====')
    args.parser = FrameParser()
    args.reader = ReaderVideo(args.relpath)

    c.execute('SELECT id,imagefile FROM cars')
    car_entries = c.fetchall()

    num_parsed = 0
    for carid,imagefile in progressbar.ProgressBar()(car_entries):
        logging.debug ('Processing car: %d' % carid)
        if _processCar (c, carid, imagefile, args.in_annotations_dir, args):
            num_parsed += 1

    logging.info('Parsed %d cars.' % num_parsed)
