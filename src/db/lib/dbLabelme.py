import os, sys, os.path as op
import numpy as np
import cv2
from lxml import etree as ET
import collections
import logging
import glob
import shutil
import sqlite3
from dbUtilities import *
from helperSetup import atcity
from annotations.parser import FrameParser, PairParser
from helperImg import ReaderVideo


def add_parsers(subparsers):
  importLabelmeParser(subparsers)


def _pointsOfPolygon (annotation):
    pts = annotation.find('polygon').findall('pt')
    xs = []
    ys = []
    for pt in pts:
        xs.append( int(pt.find('x').text) )
        ys.append( int(pt.find('y').text) )
    return xs, ys


def _processFrame (c, imagefile, annotations_dir, args):

    # get paths and names
    imagename = op.basename(imagefile)
    annotation_name = op.splitext(imagename)[0] + '.xml'
    annotation_file = atcity(op.join(annotations_dir, annotation_name))
    logging.debug ('annotation_file: ' + annotation_file)

    # if annotation file does not exist then this imagre is not annotated
    if not op.exists(atcity(annotation_file)):
        logging.debug ('this image is not annotated. Skip it.')
        return

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
        name = args.parser.parse(object_.find('name').text)
        if name == 'object':
            logging.info('skipped an "object"')
            continue
        if name is None:
            logging.info('skipped a None')
            continue

        # get all the points
        xs, ys = _pointsOfPolygon(object_)

        # replace pointers to small squares
        if len(xs) == 1:
            d = 5
            xs = [xs[0]-d, xs[0]-d, xs[0]+d, xs[0]+d]
            ys = [ys[0]+d, ys[0]-d, ys[0]-d, ys[0]+d]

        # filter out degenerate polygons
        if len(xs) == 2 or min(xs) == max(xs) or min(ys) == max(ys):
            logging.info ('degenerate polygon %s,%s in %s' % (str(xs), str(ys), annotation_name))
            continue

        # make roi
        roi = [min(ys), min(xs), max(ys), max(xs)]

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


def importLabelmeParser(subparsers):
  parser = subparsers.add_parser('importLabelme',
    description='Import labelme annotations for a db.')
  parser.set_defaults(func=importLabelme)
  parser.add_argument('--in_annotations_dir', required=True,
      help='Directory with xml files.')
  parser.add_argument('--display', action='store_true')

def importLabelme (c, args):

    logging.info ('==== importLabelme ====')
    args.parser = FrameParser()
    args.reader = ReaderVideo(args.relpath)

    c.execute('SELECT imagefile FROM images')
    imagefiles = c.fetchall()

    for imagefile, in imagefiles:
        logging.debug ('Processing imagefile: "%s"' % imagefile)
        _processFrame (c, imagefile, args.in_annotations_dir, args)

