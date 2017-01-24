import os, sys, os.path as op
import numpy as np
import cv2
import logging
import sqlite3
import datetime
from helperSetup import atcity, setParamUnlessThere, assertParamIsThere
from helperDb    import createDb, imageField
from helperImg   import ProcessorVideo


def dataset2video (c, out_image_video_file=None, out_mask_video_file=None):
  '''
  Write each frame from a db to several of files image.avi, mask.avi, time.txt
  Args:
    c - cursor
    image_video_file, mask_video_file, time_file - output file paths 
        with respect to CITY_DATA_PATH. If None, then not written.
  '''
  logging.info ('==== dataset2video ====')

  logging.info ('image file: %s' % out_image_video_file)
  logging.info ('mask file:  %s' % out_mask_video_file)

  # Assume mask field is null. Deduce the out mask name from imagefile.
  #   Also send the image video to processor, so that it deduces video params.
  c.execute('SELECT imagefile,maskfile,width,height FROM images')
  image_entries = c.fetchall()
  in_image_video_file = '%s.avi' % op.dirname(image_entries[0][0])
  in_mask_video_file  = '%s.avi' % op.dirname(image_entries[0][1])

  processor = ProcessorVideo(\
         ({'out_dataset': {in_image_video_file: out_image_video_file,
                           in_mask_video_file:  out_mask_video_file} }))

  for i, (imagefile, maskfile, _, _) in enumerate(image_entries):
    if i < 100 or i >= 4000: continue
    image = processor.imread   (imagefile)
    mask  = processor.maskread (maskfile)
    if out_image_video_file is not None: processor.imwrite   (image, imagefile)
    if out_mask_video_file  is not None: processor.maskwrite (mask, maskfile)



