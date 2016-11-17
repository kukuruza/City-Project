import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
from learning.helperSetup import atcity, dbInit, setupLogging
from learning.helperDb import imageField
from learning.helperImg import ReaderVideo
import logging
import argparse
import cv2
import numpy as np
import configs
import time


class DbReader:
  def __init__(self, db_file, use_fraction, dilate_mask, is_sequential=False):

    (conn, c) = dbInit(db_file)
    c.execute('SELECT * FROM images ORDER BY imagefile')
    self.image_entries = c.fetchall()
    conn.close()

    self.is_sequential = is_sequential

    self.image_reader = ReaderVideo()
    self.num_batches = int(len(self.image_entries) * use_fraction / configs.BATCH_SIZE)
    logging.info ('data provider has %d batches' % self.num_batches)

    self.kernel = np.ones((dilate_mask,dilate_mask), np.uint8)


  def get_next_batch(self):

    accum_time = 0

    if not self.is_sequential:
      np.random.shuffle(self.image_entries)

    for b in range(self.num_batches):
      start = time.time()

      im_shape = (configs.BATCH_SIZE, configs.IMG_SIZE[1], configs.IMG_SIZE[0], 3)
      ma_shape = (configs.BATCH_SIZE, configs.IMG_SIZE[1], configs.IMG_SIZE[0], 2)
      images = np.zeros (im_shape, dtype=float)
      masks  = np.zeros (ma_shape, dtype=float)

      # frame numbers for this batch
      iframes = range(configs.BATCH_SIZE * b, configs.BATCH_SIZE * (b+1))
      logging.debug ('minibatch iframes: %s' % ','.join([str(x) for x in iframes]))

      for i,iframe in enumerate(iframes):
        image_entry = self.image_entries[iframe]
        img  = self.image_reader.imread   (imageField(image_entry, 'imagefile'))
        mask = self.image_reader.maskread (imageField(image_entry, 'maskfile'))
        mask = cv2.dilate(mask.astype(np.uint8)*255, self.kernel, 1)
        images[i,:,:,:] = cv2.resize(img,  configs.IMG_SIZE)
        masks [i,:,:,0] = cv2.resize(mask.astype(float), configs.IMG_SIZE)

      images = (images - configs.COLOR_MEAN_BGR) / 255.0
      masks  = (masks[:,:,:,0] > 0).astype(float)

      masks = np.stack((1 - masks, masks), axis=-1)
      
      end = time.time()
      accum_time += (end - start)
      yield (images, masks)

    logging.debug ('DbReader: reading data for the epoch took %s' % str(accum_time))


if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('--db_file', required=True)
  parser.add_argument('--use_fraction', type=float, default=1.)
  parser.add_argument('--dilate_mask', type=int, default=1)
  parser.add_argument('--is_sequential', action='store_true')
  args = parser.parse_args()

  setupLogging ('log/segmentation/readData.log', logging.INFO, 'w')

  data_reader = DbReader(args.db_file, args.use_fraction, args.dilate_mask,
                         is_sequential=args.is_sequential)

  for epoch in range(3):
    logging.info('epoch %d' % (epoch+1))
    for images, masks in data_reader.get_next_batch():
      images = images * 255 + configs.COLOR_MEAN_BGR
      cv2.imshow ('image0', images[0,:,:,:].astype(np.uint8))
      cv2.imshow ('mask0_pos', masks[0,:,:,1])
      cv2.waitKey(-1)
