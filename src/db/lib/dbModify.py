import os, sys, os.path as op
from math import ceil
import numpy as np
import cv2
import logging
import sqlite3
import json
import random
from progressbar import ProgressBar
import dbUtilities
from helperDb          import createDb, deleteCar, carField, imageField, deleteCars
from helperDb          import doesTableExist, createTablePolygons
from dbUtilities       import bbox2roi, roi2bbox, bottomCenter, drawRoi
from annotations.terms import TermTree
from helperSetup       import atcity, dbInit
from helperKeys        import KeyReaderUser
from helperImg         import ReaderVideo, ProcessorVideo, SimpleWriter


def add_parsers(subparsers):
  expandBoxesParser(subparsers)
  assignOrientationsParser(subparsers)
  moveVideoParser(subparsers)
  mergeParser(subparsers)
  splitParser(subparsers)


def _expandCarBbox_ (car_entry, args):
  carid = carField(car_entry, 'id')
  roi = bbox2roi (carField(car_entry, 'bbox'))
  if args.keep_ratio:
    roi = dbUtilities.expandRoiToRatio(roi, args.expand_perc, args.target_ratio)
  else:
    roi = dbUtilities.expandRoiFloat(roi, (args.expand_perc, args.expand_perc))
  return roi


def expandBoxesParser(subparsers):
  parser = subparsers.add_parser('expandBoxes',
    description='Expand bbox in all four directions.')
  parser.set_defaults(func=expandBoxes)
  parser.add_argument('--expand_perc', type=float, default=0.0)
  parser.add_argument('--target_ratio', type=float, default=1.)  # h / w.
  parser.add_argument('--keep_ratio', action='store_true')
  parser.add_argument('--display_expand', action='store_true')

def expandBoxes (c, args):
  logging.info ('==== expandBoxes ====')

  if args.display_expand:
    key = 0
    key_reader = KeyReaderUser()
    image_reader = ReaderVideo()

  c.execute('SELECT imagefile FROM images')
  image_entries = c.fetchall()

  for (imagefile,) in ProgressBar()(image_entries):

    c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
    car_entries = c.fetchall()
    logging.debug('%d cars found for %s' % (len(car_entries), imagefile))

    if args.display_expand and key != 27:
      oldroi = bbox2roi (carField(car_entry, 'bbox'))

    for car_entry in car_entries:
      carid = carField(car_entry, 'id')
      roi = _expandCarBbox_(car_entry, args)
      s = 'x1=?, y1=?, width=?, height=?'
      c.execute('UPDATE cars SET %s WHERE id=?' % s, tuple(roi2bbox(roi) + [carid]))

    # draw roi on the 'display' image
    if args.display_expand and key != 27:
      display = image_reader.imread(imagefile)
      drawRoi (display, oldroi, '', (0,0,255))
      drawRoi (display, roi, '', (255,0,0))
      cv2.imshow('display_expand', display)
      key = key_reader.readKey()
      if key == 27:
        cv2.destroyWindow('display_expand')


def assignOrientationsParser(subparsers):
  parser = subparsers.add_parser('assignOrientations',
    description='Assign "yaw" and "pitch" to each car based on provided maps.')
  parser.set_defaults(func=assignOrientations)
  parser.add_argument('--size_map_file', required=True)
  parser.add_argument('--pitch_map_path')
  parser.add_argument('--yaw_map_path')

def assignOrientations (c, params):
  logging.info ('==== assignOrientations ====')

  assert op.exists(atcity(args.size_map_file)), atcity(args.size_map_file)
  size_map = cv2.imread(atcity(args.size_map_file), 0).astype(np.float32)
  if args.pitch_map_file:
    assert op.exists(atcity(args.pitch_map_file)), atcity(args.pitch_map_file)
    pitch_map = cv2.imread(atcity(args.pitch_map_file), 0).astype(np.float32)
  if args.yaw_map_file:
    assert op.exists(atcity(args.yaw_map_file)), atcity(args.yaw_map_file)
    yaw_map = cv2.imread(atcity(args.yaw_map_file), 0).astype(np.float32)
    # in the tiff angles belong to [0, 360). Change that to [-180, 180)
    yaw_map = np.mod((yaw_map + 180), 360) - 180.0

  c.execute('SELECT * FROM cars')
  car_entries = c.fetchall()

  for car_entry in car_entries:
    carid = carField (car_entry, 'id')
    roi = bbox2roi (carField (car_entry, 'bbox'))
    bc = bottomCenter(roi)
    if size_map[bc[0], bc[1]] > 0:
      if args.yaw_map_file:
        yaw = float(yaw_map[bc[0], bc[1]])
      if args.pitch_map_file:
        pitch = float(pitch_map[bc[0], bc[1]])
      c.execute('UPDATE cars SET yaw=?, pitch=? WHERE id=?', (yaw, pitch, carid))


def moveVideoParser(subparsers):
  parser = subparsers.add_parser('moveVideo',
    description='Move video and mask file after changing video locations.')
  parser.set_defaults(func=moveVideo)
  parser.add_argument('--image_video')
  parser.add_argument('--mask_video')

def moveVideo (c, params):
  logging.info ('==== moveVideo ====')

  if args.image_video:
    image_video = op.splitext(args.image_video)[0]  # in case there was .avi
    logging.debug ('Moving image video to: %s' % image_video)
    c.execute('SELECT imagefile FROM images')
    imagefiles = c.fetchall()

    for oldfile, in ProgressBar()(imagefiles):
      newfile = op.join (image_video, op.basename(oldfile))
      c.execute('UPDATE images SET imagefile=? WHERE imagefile=?', (newfile, oldfile))
      c.execute('UPDATE cars SET imagefile=? WHERE imagefile=?', (newfile, oldfile))

  if args.mask_video:
    mask_video = op.splitext(args.mask_video)[0]  # in case there was .avi
    logging.debug ('Moving mask video to: %s' % mask_video)
    c.execute('SELECT maskfile FROM images')
    maskfiles = c.fetchall()

    for oldfile, in ProgressBar()(maskfiles, desc='mask_dir'):
      newfile = op.join (image_video, op.basename(oldfile))
      c.execute('UPDATE images SET maskfile=? WHERE maskfile=?', (newfile, oldfile))


def mergeParser(subparsers):
  parser = subparsers.add_parser('merge',
    description='Merge images and cars from add_db_file to current database.')
  parser.set_defaults(func=merge)
  parser.add_argument('--add_db_file', required=True)
    
def merge (c, args):
  logging.info ('==== merge ====')
  (conn_add, c_add) = dbInit(args.add_db_file)

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

  conn_add.close()


def splitParser(subparsers):
  parser = subparsers.add_parser('split',
    description='Split a db into several sets (randomly or sequentially).')
  parser.set_defaults(func=split)
  parser.add_argument('--out_db_dir', default='.',
    help='Common directory for all databases relative to CITY_PATH')
  parser.add_argument('--out_db_names', required=True, nargs='+',
    help='Output database names.')
  parser.add_argument('--fractions', required=True, nargs='+', type=float,
    help='''Fractions to put to each output db.
            If percentage sums to >1, last db-s will be underfilled.''')
  parser.add_argument('--randomly', action='store_true')
    
def split (c, args):
  logging.info ('==== split ====')
  c.execute('SELECT imagefile FROM images')
  imagefiles = sorted(c.fetchall())
  if args.randomly: random.shuffle(imagefiles)

  assert len(args.out_db_names) == len(args.fractions), \
    'Sizes not equal: %d != %d' % (len(args.out_db_names), len(args.fractions))

  current = 0
  for db_out_name, fraction in zip(args.out_db_names, args.fractions):
    logging.info((db_out_name, fraction))
    num_images_in_set = int(ceil(len(imagefiles) * fraction))
    next = min(current + num_images_in_set, len(imagefiles))

    logging.info('Writing %d images to %s' % (num_images_in_set, db_out_name))
    db_out_path = atcity(op.join(args.out_db_dir, '%s.db' % db_out_name))
    if op.exists(db_out_path): os.remove(db_out_path)
    conn_out = sqlite3.connect(db_out_path)
    createDb(conn_out)
    c_out = conn_out.cursor()

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

    conn_out.commit()
    conn_out.close()

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
  
  for imagefile, in ProgressBar()(imagefiles[-num_to_remove:]):
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
