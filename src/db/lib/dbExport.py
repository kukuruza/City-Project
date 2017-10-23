import os, sys, os.path as op
import argparse
import logging
import sqlite3
import numpy as np
from tqdm import trange, tqdm
from inspect import stack
from datetime import datetime
from helperDb import carField, imageField, createDb, makeTimeString
from helperSetup import atcity
from helperImg import ReaderVideo, SimpleWriter
from dbUtilities import cropPatch


def add_parsers(subparsers):
  exportCarsToDatasetParser(subparsers)
  exportImagesWBoxesParser(subparsers)



class DatasetWriter:
  ''' Write a new dataset (db and videos). '''

  def __init__(self, out_db_file, overwrite=False):

    out_dir = op.dirname(out_db_file)
    if not op.exists(atcity(out_dir)):
      os.makedirs(atcity(out_dir))

    self.imagedir = op.join(op.relpath(out_dir, os.getenv('CITY_PATH')),
                            op.splitext(op.basename(out_db_file))[0])
    self.maskdir = self.imagedir + 'mask'
    vimagefile = self.imagedir + '.avi'
    vmaskfile = self.maskdir + '.avi'
    self.video_writer = SimpleWriter(vimagefile=vimagefile, vmaskfile=vmaskfile,
                                     unsafe=overwrite)

    if op.exists(atcity(out_db_file)):
      if overwrite:
        os.remove(atcity(out_db_file))
      else:
        raise Exception('%s already exists. A mistake?' % out_db_file)
    self.conn = sqlite3.connect(atcity(out_db_file))
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
    self.c.execute('INSERT INTO %s VALUES (?,?,?,?,?,?,?,?,?);' % s, car_entry)

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

  c.execute('SELECT * FROM cars')
  for car in tqdm(c.fetchall()):
    carid = carField(car, 'id')
    imagefile = carField(car, 'imagefile')
    roi = carField(car, 'roi')
    logging.debug ('processing %d car from imagefile %s' % (carid, imagefile))
    image = reader.imread(imagefile)
    patch = cropPatch(image, roi, args.target_height, args.target_width, args.edges)

    c.execute('SELECT * FROM images WHERE imagefile = ?', (imagefile,))
    image_entry = c.fetchone()
    timestamp = imageField(image_entry, 'timestamp')
    out_imagefile = dataset_writer.add_image(image=patch, timestamp=timestamp)
    car_entry = (out_imagefile, carField(car,'name'), 
                 0, 0, args.target_width, args.target_height,
                 carField(car,'score'), carField(car,'yaw'), carField(car,'pitch'))
    dataset_writer.add_car(car_entry)

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
  for (imagefile,) in tqdm(c.fetchall()):

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
