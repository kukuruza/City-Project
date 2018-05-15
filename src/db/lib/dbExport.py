import os, sys, os.path as op
import argparse
import logging
import sqlite3
import numpy as np
import traceback
from progressbar import ProgressBar
from inspect import stack
from datetime import datetime
from helperDb import carField, imageField, createDb, makeTimeString
from helperSetup import atcity
from helperImg import imsave, ReaderVideo, SimpleWriter
from dbUtilities import cropPatch


def add_parsers(subparsers):
  exportCarsToDatasetParser(subparsers)
  exportImagesWBoxesParser(subparsers)
  exportCarsToFolderParser(subparsers)
  exportImagesToFolderParser(subparsers)



class DatasetWriter:
  ''' Write a new dataset (db and videos). '''

  def __init__(self, out_db_file, overwrite=False):

    # If out_db_file is not absolute, it will be relative to CITY_PATH.
    db_name = op.splitext(op.basename(out_db_file))[0]
    if op.isabs(out_db_file):
      logging.info('DatasetWriter: considering "%s" as absolute path.' % out_db_file)
      out_dir = op.dirname(out_db_file)
      self.imagedir = db_name
      logging.info('DatasetWriter: imagedir is relative to db path: "%s"' % self.imagedir)
    else:
      logging.info('DatasetWriter: considering "%s" as relative to CITY_PATH.' % out_db_file)
      out_db_file = atcity(out_db_file)
      out_dir = op.dirname(out_db_file)
      self.imagedir = op.join(op.relpath(out_dir, os.getenv('CITY_PATH')), db_name)
      logging.info('DatasetWriter: imagedir is relative to CITY_PATH: "%s"' % self.imagedir)

    if not op.exists(out_dir):
      os.makedirs(out_dir)

    self.maskdir = self.imagedir + 'mask'
    vimagefile = self.imagedir + '.avi'
    vmaskfile = self.maskdir + '.avi'
    self.video_writer = SimpleWriter(vimagefile=vimagefile, vmaskfile=vmaskfile,
                                     unsafe=overwrite)

    if op.exists(out_db_file):
      if overwrite:
        os.remove(out_db_file)
      else:
        raise Exception('%s already exists. A mistake?' % out_db_file)
    self.conn = sqlite3.connect(out_db_file)
    self.c = self.conn.cursor()
    createDb(self.conn)

    self.i_image = -1

  def add_image(self, image, mask=None, timestamp=None):
    self.i_image += 1
    imagefile = op.join(self.imagedir, '%06d' % self.i_image)
    height, width = image.shape[0:2]
    if timestamp is None: timestamp = makeTimeString(datetime.now())
    maskfile = None if mask is None else op.join(self.maskdir, '%06d' % self.i_image)
    image_entry = (imagefile, width, height, maskfile, timestamp)

    s = 'images(imagefile,width,height,maskfile,time)'
    self.c.execute('INSERT INTO %s VALUES (?,?,?,?,?)' % s, image_entry)

    self.video_writer.imwrite(image)
    if mask is not None: self.video_writer.maskwrite(mask)

    return imagefile

  def add_car(self, car_entry):
    s = 'cars(imagefile,name,x1,y1,width,height,score,yaw,pitch)'
    logging.debug('Adding a new car %s' % str(car_entry))
    self.c.execute('INSERT INTO %s VALUES (?,?,?,?,?,?,?,?,?);' % s, car_entry)
    return self.c.lastrowid

  def add_match(self, car_id, match=None):
    if match is None:
      self.c.execute('SELECT MAX(match) FROM matches')
      match = self.c.fetchone()[0]
      match = match + 1 if match is not None else 0
    s = 'matches(match,carid)'
    logging.debug('Adding a new match %d for car_id %d' % (match, car_id))
    self.c.execute('INSERT INTO %s VALUES (?,?);' % s, (match, car_id))
    return match

  def close(self):
    self.conn.commit()
    self.conn.close()


def exportCarsToDatasetParser(subparsers):
  parser = subparsers.add_parser('exportCarsToDataset',
    description='Export cars to a database with only patches.')
  parser.set_defaults(func=exportCarsToDataset)
  parser.add_argument('--patch_db_file', required=True, type=str)
  parser.add_argument('--target_width', required=True, type=int)
  parser.add_argument('--target_height', required=True, type=int)
  parser.add_argument('--edges', required=True,
    choices={'distort', 'constant', 'background'},
    help='''"distort" distorts the patch to get to the desired ratio,
            "constant" keeps the ratio but pads the patch with zeros,
            "background" keeps the ratio but includes image background.''')

def exportCarsToDataset(c, args):
  logging.info('=== exportCarsToDataset ===')

  reader = ReaderVideo()
  dataset_writer = DatasetWriter(args.patch_db_file, overwrite=True)

  c.execute('SELECT * FROM cars ORDER BY id')
  for car in ProgressBar()(c.fetchall()):
    carid = carField(car, 'id')
    imagefile = carField(car, 'imagefile')
    roi = carField(car, 'roi')
    logging.debug ('processing %d car from imagefile %s' % (carid, imagefile))

    c.execute('SELECT * FROM images WHERE imagefile = ?', (imagefile,))
    image_entry = c.fetchone()
    maskfile = imageField(image_entry, 'maskfile')
    timestamp = imageField(image_entry, 'timestamp')

    try:
      image = reader.imread(imagefile)
      patch = cropPatch(image, roi, args.target_height, args.target_width, args.edges)
      if maskfile is not None:
        mask = reader.maskread(maskfile).astype(np.uint8) * 255
        maskpatch = cropPatch(mask, roi, args.target_height, args.target_width, args.edges)
        maskpatch = maskpatch > 127
      else:
        maskpatch = None

      # Add the image.
      out_imagefile = dataset_writer.add_image(
          image=patch, mask=maskpatch, timestamp=timestamp)

      # Add the car entry.
      car_entry = (out_imagefile, carField(car,'name'), 
                  0, 0, args.target_width, args.target_height,
                  carField(car,'score'), carField(car,'yaw'), carField(car,'pitch'))
      out_carid = dataset_writer.add_car(car_entry)

      # Add the match entry, if any.
      # Assume there is the matches table.
      c.execute('SELECT match FROM matches WHERE carid = ?', (carid,))
      match = c.fetchone()
      if match is not None:
        dataset_writer.add_match(out_carid, match[0])

    except Exception, e:
      traceback.print_exc()

  dataset_writer.close()



def exportImagesWBoxesParser(subparsers):
  parser = subparsers.add_parser('exportImagesWBoxes',
    description='Write video with bounding boxes.')
  parser.set_defaults(func=exportImagesWBoxes)
  parser.add_argument('--out_videofile', required=True)

def exportImagesWBoxes (c, out_videofile):
  logging.info ('==== exportImagesWBoxes ====')

  reader = ReaderVideo()
  video_writer = SimpleWriter(vimagefile=out_videofile)

  c.execute('SELECT imagefile FROM images')
  for (imagefile,) in ProgressBar()(c.fetchall()):

    frame = reader.imread(imagefile)

    c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
    for car_entry in c.fetchall():
      roi   = bbox2roi (carField(car_entry, 'bbox'))
      name  = carField (car_entry, 'name')
      score = carField (car_entry, 'score')
      logging.debug ('roi: %s, score: %s' % (str(roi), str(score)))
      drawScoredRoi (frame, roi, label=name, score=score)

    video_writer.imwrite(frame)

  video_writer.close()


def exportCarsToFolderParser(subparsers):
  parser = subparsers.add_parser('exportCarsToFolder',
    description='Export cars to a folder with only patches.')
  parser.set_defaults(func=exportCarsToFolder)
  parser.add_argument('--patch_dir', required=True, type=str)
  parser.add_argument('--target_width', required=True, type=int)
  parser.add_argument('--target_height', required=True, type=int)
  parser.add_argument('--edges', required=True,
    choices={'distort', 'constant', 'background'},
    help='''"distort" distorts the patch to get to the desired ratio,
            "constant" keeps the ratio but pads the patch with zeros,
            "background" keeps the ratio but includes image background.''')

def exportCarsToFolder(c, args):
  logging.info('=== exportCarsToFolder ===')

  reader = ReaderVideo()

  if not op.exists(atcity(args.patch_dir)):
    os.makedirs(atcity(args.patch_dir))

  c.execute('SELECT * FROM cars')
  for car in ProgressBar()(c.fetchall()):
    carid = carField(car, 'id')
    roi = carField(car, 'roi')
    imagefile = carField(car, 'imagefile')
    logging.debug ('processing %d car from imagefile %s' % (carid, imagefile))

    image = reader.imread(imagefile)
    patch = cropPatch(image, roi, args.target_height, args.target_width, args.edges)

    out_name = '%s.jpg' % op.basename(imagefile)
    out_imagefile = op.join(atcity(args.patch_dir), out_name)
    imsave(out_imagefile, patch)


def exportImagesToFolderParser(subparsers):
  parser = subparsers.add_parser('exportImagesToFolder',
    description='Export cars to a folder with only patches.')
  parser.set_defaults(func=exportImagesToFolder)
  parser.add_argument('--image_dir', required=True, type=str)
  parser.add_argument('--target_width', type=int)

def exportImagesToFolder(c, args):
  logging.info('=== exportImagesToFolder ===')
  import cv2

  reader = ReaderVideo()

  if not op.exists(atcity(args.image_dir)):
    os.makedirs(atcity(args.image_dir))

  c.execute('SELECT imagefile, width FROM images')
  for imagefile, width in ProgressBar()(c.fetchall()):
    logging.debug ('processing imagefile %s' % imagefile)

    image = reader.imread(imagefile)
    if args.target_width is not None:
      f = float(args.target_width) / width
      image = cv2.resize(image, dsize=None, fx=f, fy=f)

    out_name = '%s.jpg' % op.basename(imagefile)
    out_imagefile = op.join(atcity(args.image_dir), out_name)
    imsave(out_imagefile, image)

