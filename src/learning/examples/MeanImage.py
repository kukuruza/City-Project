#! /usr/bin/env python
import os, sys, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import cv2
import logging
import argparse
import numpy as np
from learning.helperSetup import setupLogging, dbInit, atcity
from learning.helperImg import ReaderVideo, imsave


parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--out_jpg_file', required=True)
parser.add_argument('--logging_level', default=20, type=int)

setupLogging ('log/learning/Modify.log', args.logging_level, 'a')


(conn, cursor) = dbInit (args.in_db_file, backup=False)
cursor.execute('SELECT imagefile FROM images')
imagefiles = cursor.fetchall()[:6000]
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
imsave (atcity(args.out_jpg_file), img_avg)

