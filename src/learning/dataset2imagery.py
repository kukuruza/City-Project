import os, sys, os.path as op
import numpy as np
import cv2
import logging
import sqlite3
import datetime
from tqdm import trange, tqdm
from helperSetup import atcity, setParamUnlessThere, assertParamIsThere
from helperDb    import createDb, imageField
from helperImg   import ReaderVideo, SimpleWriter
from dbUtilities import drawScoredRoi, bbox2roi
from helperDb    import carField


def exportVideoWBoxes (c, out_videofile, params = {}):
  ''' Write video with bounding boxes '''
  
  logging.info ('==== exportVideo ====')
  setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
  setParamUnlessThere (params, 'image_reader',  ReaderVideo())

  video_writer = SimpleWriter(vimagefile=out_videofile, params=params)

  c.execute('SELECT imagefile FROM images')
  for (imagefile,) in tqdm(c.fetchall()):

      frame = params['image_reader'].imread(imagefile)

      c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
      for car_entry in c.fetchall():
          roi       = bbox2roi (carField(car_entry, 'bbox'))
          imagefile = carField (car_entry, 'imagefile')
          name      = carField (car_entry, 'name')
          score     = carField (car_entry, 'score')

          logging.debug ('roi: %s, score: %s' % (str(roi), str(score)))
          # do not draw color since it's not necessary
          drawScoredRoi (frame, roi, label=name, score=score)

      video_writer.imwrite(frame)



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
    image = processor.imread   (imagefile)
    mask  = processor.maskread (maskfile)
    if out_image_video_file is not None: processor.imwrite   (image, imagefile)
    if out_mask_video_file  is not None: processor.maskwrite (mask, maskfile)



def dataset2images (c, out_image_dir=None, out_mask_dir=None):
  ''' Write each frame and mask from a db to its directories '''

  logging.info ('==== dataset2video ====')

  logging.info ('image dir: %s' % out_image_dir)
  logging.info ('mask dir:  %s' % out_mask_dir)

  # create directories
  if out_image_dir is not None:
    if not op.exists (atcity(out_image_dir)):
      os.makedirs (atcity(out_image_dir))
  if out_mask_dir is not None:
    if not op.exists (atcity(out_mask_dir)):
      os.makedirs (atcity(out_mask_dir))

  # Assume mask field is null. Deduce the out mask name from imagefile.
  #   Also send the image video to processor, so that it deduces video params.
  c.execute('SELECT imagefile,maskfile FROM images')
  image_entries = c.fetchall()

  reader = ReaderVideo()

  for imagefile, maskfile in image_entries:
    if out_image_dir is not None:
      image = reader.imread   (imagefile)
      imagepath = atcity(op.join(out_image_dir, '%s.jpg' % op.basename(imagefile)))
      logging.debug ('will write imagefile to %s' % imagepath)
      result = cv2.imwrite(imagepath, image)
    if out_mask_dir  is not None: 
      mask  = reader.maskread (maskfile)
      maskpath  = atcity(op.join(out_mask_dir, '%s.png' % op.basename(maskfile)))
      logging.debug ('will write maskpath to %s' % maskpath)
      cv2.imwrite(maskpath, mask)
