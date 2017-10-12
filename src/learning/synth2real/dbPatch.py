import os, sys, os.path as op
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import argparse
import logging
import sqlite3
import numpy as np
from tqdm import trange, tqdm
from scipy.misc import imresize
from learning.helperDb    import carField, imageField, createDb
from learning.helperSetup import dbInit, setParamUnlessThere, assertParamIsThere, atcity
from learning.helperImg   import ReaderVideo, SimpleWriter
from learning.dbUtilities import bbox2roi, expandRoiFloat


def exportCarsToDb (c, argv):
  logging.info('=== dbExportCarsNpz ===')
  parser = argparse.ArgumentParser()
  parser.add_argument('--out_db_file', required=True, type=str)
  parser.add_argument('--target_width', required=True, type=int)
  parser.add_argument('--target_height', required=True, type=int)
  args, _ = parser.parse_known_args(argv)

  out_dir = op.dirname(args.out_db_file)
  if not op.exists(atcity(out_dir)):
    os.makedirs(atcity(out_dir))

  reader = ReaderVideo()

  vimagefile = op.splitext(op.basename(args.out_db_file))[0] + '.avi'
  image_writer = SimpleWriter(vimagefile=op.join(out_dir, vimagefile))

  conn = sqlite3.connect(atcity(args.out_db_file))
  print (atcity(args.out_db_file))
  c_out = conn.cursor()
  createDb(conn)

  c.execute('SELECT * FROM cars')
  car_entries = c.fetchall()
  print (len(car_entries))

  for icar,car in enumerate(tqdm(car_entries)):
    carid = carField(car, 'id')
    imagefile = carField(car, 'imagefile')
    roi = carField(car, 'roi')
    logging.debug ('processing %d patch from imagefile %s' % (icar, imagefile))
    img = reader.imread(imagefile)
    pad=img.shape[1]
    img = np.pad(img, pad_width=((pad,pad),(pad,pad),(0,0)), mode='constant')
    patch = img[roi[0]+pad : roi[2]+pad, roi[1]+pad : roi[3]+pad]
    try:
      patch = imresize(patch, (args.target_height, args.target_width))
      image_writer.imwrite(patch)
    except ValueError:
      logging.error('Car %d from %s is bad. Patches size: %s' %
          (carid, imagefile, str(patch.shape)))

    c.execute('SELECT * FROM images WHERE imagefile = ?', (imagefile,))
    image_entry = c.fetchone()
    out_imagefile = op.join(out_dir, 'patch', '%06d' % icar)
    w = args.target_width
    h = args.target_height
    timestamp = imageField(image_entry, 'timestamp')
    out_imagefile = op.join(op.relpath(out_dir, os.getenv('CITY_PATH')), '%06d' % icar)
    s = 'images(imagefile,width,height,time)'
    c_out.execute('INSERT INTO %s VALUES (?,?,?,?)' % s,
        (out_imagefile, w, h, timestamp))
    s = 'cars(imagefile,x1,y1,width,height,name,score,yaw,pitch)'
    c_out.execute('INSERT INTO %s VALUES (?,?,?,?,?,?,?,?,?);' % s,
        (out_imagefile, 0, 0, w, h, carField(car,'name'), carField(car,'score'),
         carField(car,'yaw'), carField(car,'pitch')))

  conn.commit()
  conn.close()
