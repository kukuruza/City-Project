import os, sys, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import cv2
import logging
import numpy as np
from scipy.misc import imsave
from learning.helperSetup import setupLogging, dbInit, atcity
from learning.helperImg import ReaderVideo


setupLogging ('log/learning/Modify.log', logging.INFO, 'a')

in_db_file   = 'data/augmentation/video/cam572/Feb23-09h-Oct15/init-src.db'
out_jpg_file = 'data/augmentation/video/cam572/Feb23-09h-Oct15/mean.jpg'

(conn, c) = dbInit (in_db_file)
c.execute('SELECT imagefile FROM images')
imagefiles = c.fetchall()[:6000]
assert len(imagefiles) > 0
conn.close()

print len(imagefiles)

reader = ReaderVideo()
img_avg = None

for i,(imagefile,) in enumerate(imagefiles):
  img = reader.imread(atcity(imagefile))
  if img_avg is None:
    img_avg = np.zeros(img.shape, dtype=int)
  print img_avg.mean()
  img_avg += img
img_avg /= len(imagefiles)
img_avg = img_avg.astype(np.uint8)
imsave (atcity(out_jpg_file), img_avg)

