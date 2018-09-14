import os, sys, os.path as op
from math import ceil
import numpy as np
import logging
import sqlite3
import json
import cv2
import random
from progressbar import ProgressBar
from .helperDb          import createDb, deleteCar, carField, imageField, deleteCars
from .helperDb          import doesTableExist, createTablePolygons
from .dbUtilities       import bbox2roi, roi2bbox, bottomCenter, drawRoi
from .dbUtilities       import expandRoiToRatio, expandRoiFloat
from .annotations.terms import TermTree
from .helperSetup       import atcity, dbInit
from .helperKeys        import KeyReaderUser
from .helperImg         import ReaderVideo, ProcessorVideo, SimpleWriter


def add_parsers(subparsers):
  expandBoxesParser(subparsers)
  moveVideoParser(subparsers)
  addParser(subparsers)
  mergePolygonsIntoMaskParser(subparsers)
  splitParser(subparsers)
  moduleAnglesParser(subparsers)
  polygonsToMasksParser(subparsers)


def moduleAnglesParser(subparsers):
  parser = subparsers.add_parser('moduleAngles')
  parser.set_defaults(func=moduleAngles)

def moduleAngles(c, args):
  c.execute('SELECT * FROM cars')
  car_entries = c.fetchall()
  logging.debug('%d cars found' % len(car_entries))

  for car_entry in car_entries:
    carid = carField(car_entry, 'id')
    yaw = carField(car_entry, 'yaw')
    c.execute('UPDATE cars SET yaw=? WHERE id=?', (yaw % 360, carid))



def _expandCarBbox_ (car_entry, args):
  carid = carField(car_entry, 'id')
  roi = bbox2roi (carField(car_entry, 'bbox'))
  if args.keep_ratio:
    roi = expandRoiToRatio(roi, args.expand_perc, args.target_ratio)
  else:
    roi = expandRoiFloat(roi, (args.expand_perc, args.expand_perc))
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
    image_reader = ReaderVideo(relpath=args.relpath)

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


def addParser(subparsers):
  parser = subparsers.add_parser('add',
    description='Merge images and cars from add_db_file to current database.')
  parser.set_defaults(func=add)
  parser.add_argument('--add_db_file', required=True)
    
def add (c, args):
  logging.info ('==== add ====')
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
      logging.info ('Merge: duplicate image found %s' % imagefile) 
      continue
    # insert image
    logging.info ('Merge: insert imagefile: %s' % (imagefile,))
    c.execute('INSERT INTO images VALUES (?,?,?,?,?,?)', image_entry)
  
  # copy cars and polygons
  c_add.execute('SELECT * FROM cars')
  for car_entry_add in c_add.fetchall():

    # check if there is a car with the same ROI. Consider that a duplicate.
    imagefile = carField(car_entry_add, 'imagefile')
    c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
    car_entries_old = c.fetchall()
    for car_entry_old in car_entries_old:
      if carField(car_entry_add, 'bbox') == carField(car_entry_old, 'bbox'):
        logging.info ('Merge: duplicate car found. Adding %s to %s' % (car_entry_add, car_entry_old))
        for field in ['name', 'score', 'yaw', 'pitch', 'color']:
          carid_old = carField(car_entry_old, 'id')
          field_val_old = carField(car_entry_old, field)
          field_val_add = carField(car_entry_add, field)
          if field_val_old is None and field_val_add is not None:
            # Updating a None old value with a new value - good job, you added db.
            c.execute('UPDATE cars SET %s=? WHERE id=?' % field, (field_val_add, carid_old))
          elif field_val_old is not None and field_val_add is not None and field_val_old != field_val_add:
            logging.warning('Merge: field "%s" is conficting, skip it' % field)
        # TODO: merge masks too.
        duplicate_found = True
        break
      else:
        duplicate_found = False
    if duplicate_found:
      continue

    # insert car
    carid = carField (car_entry_add, 'id')
    s = 'cars(imagefile,name,x1,y1,width,height,score,yaw,pitch,color)'
    c.execute('INSERT INTO %s VALUES (?,?,?,?,?,?,?,?,?,?)' % s, car_entry_add[1:])
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


def polygonsToMasksParser(subparsers):
  parser = subparsers.add_parser('polygonsToMasks',
    description='Convert polygons in db to mask video.' +
    'If there is not polygons for any car in an image, an empty mask is written.')
  parser.set_defaults(func=polygonsToMasks)
  parser.add_argument('--mask_name', default='mask-poly.avi')
  parser.add_argument('--write_null_mask_entries', action='store_true',
    help='Write null when there is no new mask.')
  parser.add_argument('--overwrite_video', action='store_true',
    help='Overwrte mask video istead of throwing an exception.')
    
def polygonsToMasks (c, args):
  logging.info ('==== polygonsToMasks ====')

  # Assume mask field is null. Deduce the out mask name from imagefile.
  c.execute('SELECT imagefile,width,height FROM images')
  image_entries = c.fetchall()
  in_image_video_file = '%s.avi' % op.dirname(image_entries[0][0])
  out_mask_video_file = '%s/%s' % (op.dirname(in_image_video_file), args.mask_name)
  logging.info ('polygonsToMasks: in_image_video_file: %s' % in_image_video_file)
  logging.info ('polygonsToMasks: out_mask_video_file: %s' % out_mask_video_file)

  video_writer = SimpleWriter(vmaskfile=out_mask_video_file, unsafe=args.overwrite_video)

  count = 0
  for imagefile, width, height in ProgressBar()(image_entries):
    
    logging.debug('imagefile: "%s"' % imagefile)
    mask = np.zeros((height, width), dtype=np.uint8)
    c.execute('SELECT id FROM cars WHERE imagefile=? INTERSECT SELECT carid FROM polygons', (imagefile,))
    carids = c.fetchall()
    logging.debug('found %d cars with polygons for this imagefile' % len(carids))
    for carid, in carids:
      c.execute('SELECT x,y FROM polygons WHERE carid = ?', (carid,))
      polygon_entries = c.fetchall()
      pts = [[pt[0], pt[1]] for pt in polygon_entries]
      cv2.fillConvexPoly(mask, np.asarray(pts, dtype=np.int32), 255)
    mask = mask > 0
    maskfile = video_writer.maskwrite (mask)
    if len(carids) > 0:
      logging.debug('imagefile has polygons: "%s"' % imagefile)
      count += 1
      c.execute('UPDATE images SET maskfile=? WHERE imagefile=?', (maskfile, imagefile))
    elif args.write_null_mask_entries:
      c.execute('UPDATE images SET maskfile=? WHERE imagefile=?', (None, imagefile))
  
  logging.info('Found %d images with polygons.' % count)


def mergePolygonsIntoMaskParser(subparsers):
  parser = subparsers.add_parser('mergePolygonsIntoMask',
    description='Merge multiple polygons of the same car into one '
    'and in parallel convert them into a *gray* mask for that car. '
    'Each polygon is taken from one db, so multiple dbs are taken as input. '
    'Cars are merged based on car_id. '
    'The number of shades of gray in the mask is the number of car entries in dbs. '
    'This function looks composite, but it cant be disassembled.')
  parser.set_defaults(func=mergePolygonsIntoMask)
  parser.add_argument('--add_db_files', nargs='+', required=True)
  parser.add_argument('--out_mask_video_file', required=True)
  parser.add_argument('--min_merges_per_image', default=0, type=int,
    help='Require a minimum number of objects to be merged into one.')
  parser.add_argument('--overwrite_video', action='store_true',
    help='Overwrite mask video istead of throwing an exception.')


def mergePolygonsIntoMask (c, args):
  logging.info ('==== mergePolygonsIntoMask ====')

  c.execute('SELECT imagefile,width,height FROM images')
  image_entries = c.fetchall()

  video_writer = SimpleWriter(vmaskfile=args.out_mask_video_file, unsafe=args.overwrite_video)

  conn_add_list = []
  c_list = [c]  # Put our cursor as the only element.
  for add_db_file in args.add_db_files:
    (conn_add, c_add) = dbInit(add_db_file)
    conn_add_list.append(conn_add)
    c_list.append(c_add)

  for imagefile, width, height in ProgressBar()(image_entries):
    
    logging.debug('Imagefile: %s' % imagefile)
    mask_sum = np.zeros((height, width), dtype=np.int32)  # int32 to accumulate uint8 masks.

    # Get all the cars.
    c.execute('SELECT id FROM cars WHERE imagefile=?', (imagefile,))
    carids_main = c.fetchall()
    logging.debug('Main db has %d cars: %s' % (len(carids_main), carids_main))

    # Get all the cars with polygons.
    c.execute('SELECT id FROM cars WHERE imagefile=? INTERSECT SELECT carid FROM polygons', (imagefile,))
    carids_main_with_poly = c.fetchall()

    # Each car for this imagefile is in at least one of the dbs, maybe not in 'c'.
    count_masks = 0
    for idb,c_add in enumerate(c_list):
      c_add.execute('SELECT id FROM cars WHERE imagefile=? INTERSECT SELECT carid FROM polygons', (imagefile,))
      carids = c_add.fetchall()
      assert len(carids) <= 1, 'Cant have %d cars in an image with current logic, only 1.' % len(carids)
      if len(carids) == 0:
        continue
      carid = carids[0][0]
      count_masks += 1
      logging.debug('Db %d: found car %s with polygons for this imagefile' % (idb, carids))
      # Add to mask.
      c_add.execute('SELECT x,y FROM polygons WHERE carid = ?', (carid,))
      polygon_entries = c_add.fetchall()
      pts = [[pt[0], pt[1]] for pt in polygon_entries]
      mask = np.zeros((height, width), dtype=np.int32)
      cv2.fillConvexPoly(mask, np.asarray(pts, dtype=np.int32), 255)
      mask_sum += mask
      # Insert into 'cars' table of main db, if not there.
      if carid not in [carid for carid, in carids_main]:
        logging.debug('Inserting carid %d into "cars" table of the main db')
        # Pull all the info about carid from c_add.
        c_add.execute('SELECT * FROM cars WHERE id=?', (carid,))
        car_entry = c_add.fetchone()
        # Insert.
        s = 'cars(imagefile,name,x1,y1,width,height,score,yaw,pitch,color)'
        c.execute('INSERT INTO %s VALUES (?,?,?,?,?,?,?,?,?,?)' % s, car_entry[1:])
        carid = c.lastrowid[0]

    if count_masks < args.min_merges_per_image:
      c.execute('DELETE FROM cars WHERE imagefile=?', (imagefile,))
      c.execute('DELETE FROM images WHERE imagefile=?', (imagefile,))
      logging.debug('Only merged objects for this image %d. Remove image entry.' % count_masks)
    mask_sum = (mask_sum / count_masks).astype(np.uint8)
    logging.debug('Number of merged objects for this image: %d' % count_masks)
    maskfile = video_writer.maskwrite(mask_sum)
    c.execute('UPDATE images SET maskfile=? WHERE imagefile=?', (maskfile, imagefile))

  for conn_add in conn_add_list:
    conn_add.close()
  video_writer.close()


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
def generateBackground (c, out_videofile, params={}):
  ''' Generate background video using mask and update imagefiles in db. '''

  logging.info ('==== polygonsToMasks ====')
  setParamUnlessThere (params, 'relpath',       os.getenv('CITY_DATA_PATH'))
  setParamUnlessThere (params, 'show_debug',    False)
  setParamUnlessThere (params, 'key_reader',    KeyReaderUser())
  setParamUnlessThere (params, 'image_reader',  ReaderVideo(relpath=args.relpath))
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

