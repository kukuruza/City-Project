import sys, os, os.path as op
sys.path.insert(0, '/Users/evg/src/tensorflow-fcn')
import tensorflow as tf
import argparse

import numpy as np
import tensorflow as tf
import time
import os
import argparse
import configs
from readData import DbReader

import skimage
import skimage.io
import skimage.transform

import os
import scipy as scp
import scipy.misc

import numpy as np
import tensorflow as tf

import fcn32_vgg
import loss
import utils



def train(train_data, test_data, init_model_path,
          lr, num_epochs, output_dir, pos_weight, save_every_nth):

  input_shape = [configs.BATCH_SIZE, configs.IMG_SIZE[1], configs.IMG_SIZE[0]]
  ph_x = tf.placeholder(tf.float32, input_shape + [3])
  ph_y = tf.placeholder(tf.float32, input_shape + [2])

  vgg_fcn = fcn32_vgg.FCN32VGG(init_model_path)
  with tf.name_scope("content_vgg"):
    vgg_fcn.build(ph_x, train=True, num_classes=2, random_init_fc8=True, debug=True)
  print('Finished building Network.')

  # # average ground truth
  # avgpred = tf.reduce_mean(preds[:,:,:,:,0])
  # avggt   = tf.reduce_mean(ph_y[:,:,:,:,0])

  # loss and train_step operations
  lss = loss.loss (vgg_fcn.upscore, ph_y, 2, pos_weight)
  opt = tf.train.GradientDescentOptimizer(lr)
  train_step = opt.minimize(lss)

  saver = tf.train.Saver()

  with tf.Session() as sess:
    sess.run(tf.initialize_all_variables())

    for epoch in range(num_epochs):
      print 'epoch:', epoch+1

      # train
      ls = np.zeros(train_data.num_batches)
      for b in range(train_data.num_batches):
        xs, ys = train_data.get_next_batch()
        ls[b], _ = sess.run([lss, train_step], feed_dict={ph_x: xs, ph_y: ys})
      print 'train loss:', ls.mean() #, 'avgpred:', avgpred_val

      # test
      ls = np.zeros(test_data.num_batches)
      for b in range(test_data.num_batches):
        xs, ys = test_data.get_next_batch()
        ls[b] = sess.run(lss, feed_dict={ph_x: xs, ph_y: ys})
      print 'test loss: ', ls.mean()

      # save
      if epoch % save_every_nth == 0 and output_dir is not None:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        save_path = saver.save(
            sess, os.path.join(output_dir, 'epoch%05d.ckpt' % epoch))
        print '\tModel saved to:', save_path



if __name__ == '__main__':
    np.random.seed(2016)
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--init_model_path', required=True)
    parser.add_argument('--out_dir',         required=True)
    parser.add_argument('--train_db_file',   required=True)
    parser.add_argument('--test_db_file',    required=False)
    parser.add_argument('--lr', type=float, default=0.001)
    parser.add_argument('--pos_weight', type=float, default=0.5)
    parser.add_argument('--num_epochs', type=int, default=30)
    parser.add_argument('--save_every_nth', type=int, default=100)
    parser.add_argument('--train_fraction', type=float, default=1.,
                        help='for debugging, use only a fraction of data for epoch')
    parser.add_argument('--test_fraction', type=float, default=1.,
                        help='for debugging, use only a fraction of data to test')
    args = parser.parse_args()

    train_data = DbReader(args.train_db_file, use_fraction=args.train_fraction)
    test_data  = DbReader(args.test_db_file,  use_fraction=args.test_fraction)

    train(train_data, test_data, args.init_model_path,
          args.lr, args.num_epochs, args.out_dir, pos_weight=args.pos_weight,
          save_every_nth=args.save_every_nth)
