import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('HOME'), 'src/tensorflow-fcn'))
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import argparse
import logging

import skimage
import skimage.io
import skimage.transform

import scipy as scp
import scipy.misc

import numpy as np
import cv2
import tensorflow as tf

import configs
from readData import DbReader

import fcn32_vgg
import loss
import utils

from learning.helperSetup import setupLogging



class VideoWriter:
  def __init__(self, out_video_path):
    self.out_video_path = out_video_path
    self.video = None


  def _open_video (self, frame):
    fourcc = 1196444237
    fps = 2
    frame_size = (frame.shape[1], frame.shape[0])
    self.video = cv2.VideoWriter (self.out_video_path, 
      fourcc, fps, frame_size, False)


  def write_next_batch (self, images):
    for image in images:
      if self.video is None: 
        self._open_video(image)
      self.video.write(image)



def test (test_data, init_npy_path, checkpoint_path,
          out_video_path, pos_weight):

  video_writer = VideoWriter(out_video_path)

  input_shape = [configs.BATCH_SIZE, configs.IMG_SIZE[1], configs.IMG_SIZE[0]]
  ph_x = tf.placeholder(tf.float32, input_shape + [3])
  ph_y = tf.placeholder(tf.float32, input_shape + [2])

  vgg_fcn = fcn32_vgg.FCN32VGG(init_npy_path)
  with tf.name_scope("content_vgg"):
    vgg_fcn.build(ph_x, train=True, num_classes=2, 
                  random_init_fc8=True, debug=True)
  logging.info('finished building Network.')

  saver = tf.train.Saver()

  with tf.Session() as sess:
    sess.run(tf.initialize_all_variables())

    if not op.exists(checkpoint_path):
      raise Exception('checkpoint_path does not exist: %s' % checkpoint_path)
    saver.restore(sess, checkpoint_path)
    logging.info('model restored from %s' % checkpoint_path)

    for b, (xs, ys) in enumerate(test_data.get_next_batch()):
      heatmap = sess.run(vgg_fcn.heatmap, feed_dict={ph_x: xs})
      video_writer.write_next_batch ((heatmap[:,:,:,1]*255).astype(np.uint8))



if __name__ == '__main__':
  np.random.seed(2016)
  
  parser = argparse.ArgumentParser()
  parser.add_argument('--init_npy_path',   required=True)
  parser.add_argument('--checkpoint_path', required=True)
  parser.add_argument('--out_video_path',  required=False)
  parser.add_argument('--test_db_file',    required=False)
  parser.add_argument('--pos_weight',      type=float, default=0.5)
  parser.add_argument('--dilate_mask',     type=int, default=1)
  parser.add_argument('--test_fraction',   type=float, default=1.)
  args = parser.parse_args()

  setupLogging('log/segmentation/test.log', 20, 'a')

  test_data = DbReader(args.test_db_file, args.test_fraction, 
                       args.dilate_mask, is_sequential=True)

  test (test_data, args.init_npy_path, args.checkpoint_path,
        args.out_video_path, pos_weight=args.pos_weight)
