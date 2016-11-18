import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('HOME'), 'src/tensorflow-fcn'))
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import argparse
import logging
import time

import skimage
import skimage.io
import skimage.transform

import scipy as scp
import scipy.misc

import numpy as np
import tensorflow as tf

import configs
from readData import DbReader

import fcn32_vgg
import loss
import utils

from learning.helperSetup import setupLogging



def train(train_data, test_data, init_npy_path,
          lr, num_epochs, output_dir, pos_weight, save_every_nth,
          checkpoint_path=None):

  input_shape = [configs.BATCH_SIZE, configs.IMG_SIZE[1], configs.IMG_SIZE[0]]
  ph_x = tf.placeholder(tf.float32, input_shape + [3])
  ph_y = tf.placeholder(tf.float32, input_shape + [2])

  vgg_fcn = fcn32_vgg.FCN32VGG(init_npy_path)
  with tf.name_scope("content_vgg"):
    vgg_fcn.build(ph_x, num_classes=2, random_init_fc8=True, debug=True)
  logging.info('finished building Network.')

  # average ground truth
  avgpred = tf.reduce_mean(tf.to_float(vgg_fcn.pred))
  # avggt   = tf.reduce_mean(ph_y)

  # loss and train_step operations
  lss = loss.loss (vgg_fcn.upscore, ph_y, 2, pos_weight)
  opt = tf.train.GradientDescentOptimizer(lr)
  train_step = opt.minimize(lss)

  saver = tf.train.Saver()

  with tf.Session() as sess:
    sess.run(tf.initialize_all_variables())

    if checkpoint_path is not None:
      if not op.exists(checkpoint_path):
        raise Exception('checkpoint_path does not exist: %s' % checkpoint_path)
      saver.restore(sess, checkpoint_path)
      logging.info('model restored from %s' % checkpoint_path)

    for epoch in range(num_epochs):

      # train
      lss_train     = np.zeros(train_data.num_batches)
      avgpred_train = np.zeros(train_data.num_batches)
      start_train = time.time()
      for b, (xs, ys) in enumerate(train_data.get_next_batch()):
        lss_train[b], avgpred_train[b], _ = \
            sess.run([lss, avgpred, train_step],
                     feed_dict={ph_x: xs, ph_y: ys, vgg_fcn.is_train_phase: True})
      logging.debug ('training the epoch took %s' % str(time.time() - start_train))

      # test
      lss_test     = np.zeros(test_data.num_batches)
      avgpred_test = np.zeros(test_data.num_batches)
      start_train = time.time()
      for b, (xs, ys) in enumerate(test_data.get_next_batch()):
        lss_test[b], avgpred_test[b] = \
            sess.run([lss, avgpred],
                     feed_dict={ph_x: xs, ph_y: ys, vgg_fcn.is_train_phase: False})
      logging.debug ('testing the epoch took %s' % str(time.time() - start_train))

      logging.info ('epoch, train avgpred, test avgpred: %s %0.4f %0.4f' % 
                    (str(epoch+1), avgpred_train.mean(), avgpred_test.mean()))
      logging.info ('epoch, train loss, test loss: %s %0.4f %0.4f' % 
                    (str(epoch+1), lss_train.mean(), lss_test.mean()))

      # save
      if (epoch+1) % save_every_nth == 0 and output_dir is not None:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        save_path = saver.save(
            sess, os.path.join(output_dir, 'epoch%05d.ckpt' % epoch))
        logging.info ('\tmodel saved to: %s' % save_path)



if __name__ == '__main__':
  np.random.seed(2016)
  
  parser = argparse.ArgumentParser()
  parser.add_argument('--init_npy_path', required=True)
  parser.add_argument('--checkpoint_path', required=False, 
                      help='continue training from there if given')
  parser.add_argument('--out_dir',         required=False)
  parser.add_argument('--train_db_file',   required=True)
  parser.add_argument('--test_db_file',    required=False)
  parser.add_argument('--lr', type=float, default=0.001)
  parser.add_argument('--pos_weight', type=float, default=0.5)
  parser.add_argument('--num_epochs', type=int, default=30)
  parser.add_argument('--save_every_nth', type=int, default=100)
  parser.add_argument('--train_fraction', type=float, default=1.,
                      help='for debugging, use only a fraction of data in epoch')
  parser.add_argument('--test_fraction', type=float, default=1.,
                      help='for debugging, use only a fraction of data to test')
  parser.add_argument('--dilate_mask', type=int, default=1)
  args = parser.parse_args()

  setupLogging('log/segmentation/train.log', 20, 'a')
  logging.info ('will save every %d iterations' % args.save_every_nth)

  train_data = DbReader(args.train_db_file, args.train_fraction, args.dilate_mask)
  test_data  = DbReader(args.test_db_file,  args.test_fraction,  args.dilate_mask)

  train(train_data, test_data, args.init_npy_path,
        args.lr, args.num_epochs, args.out_dir, pos_weight=args.pos_weight,
        save_every_nth=args.save_every_nth, checkpoint_path=args.checkpoint_path)
