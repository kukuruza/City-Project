# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import datetime
import os, os.path
import time
import math
import argparse

import numpy as np
from sklearn.metrics import confusion_matrix
from six.moves import xrange  # pylint: disable=redefined-builtin
import tensorflow as tf

import citycam

np.set_printoptions(precision=2)
np.set_printoptions(suppress=True)

FLAGS = tf.app.flags.FLAGS

tf.app.flags.DEFINE_boolean('log_device_placement', False,
                            """Whether to log device placement.""")
tf.app.flags.DEFINE_float('wd', 0.01, 'weight_decay for all fc layers')



def evaluate_clas (sess, predict, correct, labels, keep_prob):
  """Convenience function to run evaluation for for every batch. 
     Sum the number of correct predictions and output one precision value.
  Args:
    sess:      current Session
    labels:    2D Tensor of shape [batch_size], values in range [0,NUM_CLASSES)
    keep_prob: scalar Tensor placeholder. Always equals 1 (for evaluation)
  """
  num_iter = int(math.ceil(FLAGS.num_eval_examples / FLAGS.batch_size))
  true_count = 0  # Counts the number of correct predictions.
  total_sample_count = num_iter * FLAGS.batch_size

  predict_list = []
  labels_list  = []

  for step in xrange(num_iter):

    [correct_val, predict_val, labels_val] = sess.run([correct, predict, labels],
                                                       feed_dict={keep_prob: 1.0})
    true_count   += np.sum(correct_val)
    predict_list += predict_val.tolist()
    labels_list  += labels_val.tolist()

  print (confusion_matrix(np.array(predict_list), np.array(labels_list)))
  return true_count / total_sample_count



def train():
  setnames = FLAGS.setnames.split(',')
  print ('setnames: %s' % setnames)

  with tf.Graph().as_default() as graph:
    global_step = tf.Variable(0, trainable=False, name='global_step')

    images = {}
    labels = {}
    rois   = {}
    masks  = {}

    # Get images and labels for citycam.
    for sn in setnames:
      with tf.name_scope(sn):
        list_name = '%s.txt' % sn
        if sn.find('labelme') >= 0:
          print ('sn: %s, using "input()"' % sn)
          images[sn], labels[sn], rois[sn], masks[sn] = citycam.inputs(list_name)
        else:
          print ('sn: %s, using "distorted_inputs()"' % sn)
          images[sn], labels[sn], rois[sn], masks[sn] = citycam.distorted_inputs(list_name)

    # Build a Graph that computes the logits predictions from the inference model.
    with tf.variable_scope("inference") as scope:
      logits = {}
      regress = {}
      summary_prec = {}

      keep_prob = tf.placeholder(tf.float32) # for dropout

      for sn in setnames:
        logits[sn], regress[sn], _, _ = \
          citycam.inference(images[sn], keep_prob, wd=FLAGS.wd)
        scope.reuse_variables()

        summary_prec[sn] = tf.placeholder(tf.float32)
        tf.scalar_summary('precision/%s' % sn, summary_prec[sn])

        kernel = citycam.put_kernels_on_grid(tf.get_variable('conv1/weights'), (4,8))

    # Image summary of kernels, masks, rois
    with tf.name_scope('visualization'):
      # visualize conv1 filters
      tf.image_summary('conv1', kernel, max_images=1)
      # visualize images with rois and masks
      for sn in setnames:
        citycam.my_image_summary (images[sn], masks[sn], rois[sn], sn)

    # Calculate loss.
    with tf.name_scope('train'):
      sn = setnames[0]
      assert rois[sn].get_shape()[1] == 4
      loss_clas = citycam.loss_clas (logits[sn], labels[sn])
      loss_regr = citycam.loss_regr (regress[sn], rois[sn])
      loss = tf.add_n(tf.get_collection('losses'), name='total_loss')

    # Build a Graph that trains the model with one batch of examples and
    # updates the model parameters.
    train_op = citycam.train(loss, global_step)

    # Build the summary operation based on the TF collection of Summaries.
    summary_op = tf.merge_all_summaries()

    # After this step the graph will already be recorded for Tensorboard
    summary_writer = tf.train.SummaryWriter(FLAGS.train_dir,
                                            graph_def=graph.as_graph_def())

    # Create a saver for all variables
    saver = tf.train.Saver(tf.all_variables())

    # Restore the moving average version of the learned variables for eval.
    ema = tf.train.ExponentialMovingAverage(citycam.MOVING_AVERAGE_DECAY)
    restorer = tf.train.Saver(ema.variables_to_restore())

    # Will be used in evaluations
    predicts = {}
    corrects = {}
    for sn in setnames:
      corrects[sn] = tf.nn.in_top_k (logits[sn], labels[sn], 1)
      predicts[sn] = tf.argmax (logits[sn], 1, 'highest_pred')


    #######    The graph is built by this point   #######


    with tf.Session() as sess:

      # Start running operations on the Graph.
      init = tf.initialize_all_variables()
      sess.run(init)

      # Restore previous training, if provided with restore_from_dir.
      #   In this case values of initialized variables will be replaced
      if FLAGS.restore_from_dir is not None:

        ckpt = tf.train.get_checkpoint_state(FLAGS.restore_from_dir)
        if ckpt and ckpt.model_checkpoint_path:
          # Restores from checkpoint
          restorer.restore(sess, ckpt.model_checkpoint_path)
          restored_step = ckpt.model_checkpoint_path.split('/')[-1].split('-')[-1]
          print ('Restored the model from step %s' % restored_step)
        else:
          raise Exception('No checkpoint file found in %s' % FLAGS.restore_from_dir)

      # Start the queue runners.
      coord = tf.train.Coordinator()
      threads = tf.train.start_queue_runners(sess=sess, coord=coord)

      with coord.stop_on_exception():
        for step in xrange(FLAGS.max_steps):
          if coord.should_stop(): 
            break

          start_time = time.time()
          _, loss_val = sess.run([train_op, loss], feed_dict={keep_prob: 0.5})
          duration = time.time() - start_time

          assert not np.isnan(loss_val), 'Model diverged with loss = NaN'

          if step % FLAGS.period_print == 0:
            print ('%s: step %d, loss = %.2f (%.1f examples/sec; %.3f sec/batch)' %
                    (datetime.now(), step, loss_val, 
                     FLAGS.batch_size / float(duration), float(duration)))

          if step % FLAGS.period_evaluate == 0:
            summary_feed_dict = {keep_prob: 1}
            for sn in setnames:
              prec = evaluate_clas (sess, predicts[sn], corrects[sn], labels[sn], keep_prob)
              summary_feed_dict[summary_prec[sn]] = prec
              print('%s: prec %s = %.3f' % (datetime.now(), sn, prec))
            # print('regr_train_val: \n', regr_train_val[:8])
            # print('regr_loss_val: \n', regression_loss_val[:8])

          if step % FLAGS.period_summary == 0:
            summary_str = sess.run(summary_op, feed_dict=summary_feed_dict)
            summary_writer.add_summary(summary_str, step)

          if step % FLAGS.period_checkpoint == 0 or (step + 1) == FLAGS.max_steps:
            checkpoint_path = os.path.join(FLAGS.train_dir, 'model.ckpt')
            saver.save(sess, checkpoint_path, global_step=global_step)

      coord.request_stop()
      coord.join(threads, stop_grace_period_secs=10)





def main(argv=None):  # pylint: disable=unused-argument
  if FLAGS.restore_from_dir is not None and FLAGS.restore_from_dir == FLAGS.train_dir:
    raise Exception ('For now cant continue training in the same dir')
  if tf.gfile.Exists(FLAGS.train_dir):
    tf.gfile.DeleteRecursively(FLAGS.train_dir)
  tf.gfile.MakeDirs(FLAGS.train_dir)
  train()


if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  parser.add_argument('--train_dir', default='log/tensorflow/classifier_train',
                      help='Directory where to write event logs and checkpoint.')
  parser.add_argument('--restore_from_dir', default=None,
                      help='Directory where to read model checkpoints. '
                           'None by default means train from scratch.')
  parser.add_argument('--max_steps', default=1000, type=int,
                      help='Number of batches to run.')
  parser.add_argument('--num_eval_examples', default=128, type=int,
                      help='Number of examples for evaluation')
  parser.add_argument('--period_print', default=10, type=int)
  parser.add_argument('--period_summary', default=100, type=int)
  parser.add_argument('--period_evaluate', default=100, type=int)
  parser.add_argument('--period_checkpoint', default=1000, type=int)
  parser.add_argument('--list_names', nargs='+', 
                      help='multiple names of datasets, e.g. train_list.txt. '
                           'By convention, the first in the list is to train, '
                           'ones with "labelme" in name are not distorted now')
  parser.add_argument('--batch_size', default=128, type=int,
                      help='Number of images to process in a batch.')
  parser.add_argument('--lambda_regr', default=0.5, type=float)
  parser.add_argument('--data_dir', default='augmentation/patches',
                      help='Path to the citycam data directory.')
  parser.add_argument('--num_preprocess_threads', default=16, type=int)
  args = parser.parse_args()

  def atcity(x):
    return None if x is None else os.path.join(os.getenv('CITY_PATH'), x)
  def atcitydata(x):
    return None if x is None else os.path.join(os.getenv('CITY_DATA_PATH'), x)

  tf.app.flags.DEFINE_integer('period_print', args.period_print, '')
  tf.app.flags.DEFINE_integer('period_summary', args.period_summary, '')
  tf.app.flags.DEFINE_integer('period_evaluate', args.period_summary, '')
  tf.app.flags.DEFINE_integer('period_checkpoint', args.period_checkpoint, '')

  tf.app.flags.DEFINE_string('data_dir', atcitydata(args.data_dir), '')
  tf.app.flags.DEFINE_string('setnames', ','.join(args.list_names), '')
  tf.app.flags.DEFINE_string('train_dir', atcity(args.train_dir), '')
  tf.app.flags.DEFINE_string('restore_from_dir', atcity(args.restore_from_dir), '')
  tf.app.flags.DEFINE_integer('max_steps', args.max_steps, '')
  tf.app.flags.DEFINE_integer('num_eval_examples', args.num_eval_examples, '')
  tf.app.flags.DEFINE_integer('batch_size', args.batch_size, '')
  tf.app.flags.DEFINE_float('lambda_regr', args.lambda_regr, '')

  tf.app.flags.DEFINE_integer('num_preprocess_threads', args.num_preprocess_threads, '')

  tf.app.run()
