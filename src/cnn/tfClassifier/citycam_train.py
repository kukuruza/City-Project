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



def evaluate_set (sess, (correct, predicted, labels), (regressions, rois), keep_prob):
  """Convenience function to run evaluation for for every batch. 
     Sum the number of correct predictions and output one precision value.
  Args:
    sess:      current Session
    (correct, predicted, labels):  helper graph nodes
  """
  num_iter = int(math.ceil(FLAGS.num_eval_examples / FLAGS.batch_size))
  true_count = 0  # Counts the number of correct predictions.
  total_sample_count = num_iter * FLAGS.batch_size

  predicted_list = []
  labels_list    = []

  for step in xrange(num_iter):

    [correct_val, predicted_val, labels_val] = sess.run([correct, predicted, labels],
                                                        feed_dict={keep_prob: 1.0})
    #print (correct_val)
    #print (predicted_val)
    #print (labels_val)

    true_count     += np.sum(correct_val)
    predicted_list += predicted_val.tolist()
    labels_list    += labels_val.tolist()

  print (confusion_matrix(np.array(predicted_list), np.array(labels_list)))

  # Compute precision
  return true_count / total_sample_count




def train():

  with tf.Graph().as_default() as graph:
    global_step = tf.Variable(0, trainable=False, name='global_step')

    # Get images and labels for citycam.
    with tf.name_scope("train_images"): 
      images, labels, rois_train, _, images_disp = citycam.distorted_inputs(FLAGS.train_list_name)
    with tf.name_scope("eval_images"): 
      images_eval, labels_eval, rois_eval, _, _ = citycam.distorted_inputs(FLAGS.eval_list_name)
    with tf.name_scope("test_images"): 
      images_test, labels_test, rois_test, _, _ = citycam.inputs(FLAGS.test_list_name)

    # Build a Graph that computes the logits predictions from the inference model.
    with tf.variable_scope("inference") as scope:

      keep_prob = tf.placeholder(tf.float32) # dropout (keep probability)

      logits, regr_train, _     = citycam.inference(images, keep_prob, wd=FLAGS.wd)
      scope.reuse_variables()
      logits_eval, regr_eval, _ = citycam.inference(images_eval, keep_prob, wd=FLAGS.wd)
      logits_test, regr_test, _ = citycam.inference(images_test, keep_prob, wd=FLAGS.wd)

      predict_ops      = citycam.predict(logits,      labels)
      predict_eval_ops = citycam.predict(logits_eval, labels_eval)
      predict_test_ops = citycam.predict(logits_test, labels_test)

      localized_tr     = citycam.localize(regr_train, rois_train)
      localized_ev     = citycam.localize(regr_eval,  rois_eval)
      localized_te     = citycam.localize(regr_test,  rois_test)

      summary_train_prec = tf.placeholder(tf.float32)
      summary_eval_prec  = tf.placeholder(tf.float32)
      summary_test_prec  = tf.placeholder(tf.float32)
      tf.scalar_summary('precision/train.', summary_train_prec)
      tf.scalar_summary('precision/eval.', summary_eval_prec)
      tf.scalar_summary('precision/test.', summary_test_prec)

      with tf.name_scope('visualization'):
        kernel = citycam.put_kernels_on_grid(tf.get_variable('conv1/weights'), (8,8))
        tf.image_summary('conv1', kernel, max_images=1)

    # Calculate loss.
    with tf.name_scope('train'):
      assert rois_train.get_shape()[1] == 4
      loss, regression_loss = citycam.loss(logits, regr_train, labels, rois_train)

      # Build a Graph that trains the model with one batch of examples and
      # updates the model parameters.
      train_op = citycam.train(loss, global_step)

      with tf.name_scope('visualization'):
        regr_tr_disp = tf.expand_dims(regr_train, 1)  # from [batch_size,4] to [batch_size,1,4]
        images_disp = tf.image.draw_bounding_boxes(images_disp, regr_tr_disp / 2)
        images_disp = tf.pad(images_disp, [[0,0],[4,4],[4,4],[0,0]])
        tf.image_summary('images/train', images_disp, max_images=3)


    # Create a saver.
    saver = tf.train.Saver(tf.all_variables())

    # Build the summary operation based on the TF collection of Summaries.
    summary_op = tf.merge_all_summaries()

    # After this step the graph will already be recorded for Tensorboard
    summary_writer = tf.train.SummaryWriter(FLAGS.train_dir,
                                            graph_def=graph.as_graph_def())



    #######    The graph is built by this point   #######


    with tf.Session() as sess:

      # Start running operations on the Graph.
      init = tf.initialize_all_variables()
      sess.run(init)

      # Restore previous training, if provided with restore_from_dir.
      #   In this case values of initialized variables will be replaced
      if FLAGS.restore_from_dir is not None:

        # Restore the moving average version of the learned variables for eval.
    #        variable_averages = tf.train.ExponentialMovingAverage(
    #            citycam.MOVING_AVERAGE_DECAY)
    #        variable_averages.variables_to_restore()
        restorer = tf.train.Saver([v for v in tf.all_variables() if
                                   v.name.find('conv') > 0 or 
                                   v.name.find('norm') > 0 or
                                   v.name.find('pool') > 0])

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
          _, loss_value, regr_train_val, regression_loss_val = sess.run(
                  [train_op, loss, regr_train, regression_loss], 
                  feed_dict={keep_prob: 0.5})
          duration = time.time() - start_time

          assert not np.isnan(loss_value), 'Model diverged with loss = NaN'

          if step % FLAGS.period_print == 0:
            num_examples_per_step = FLAGS.batch_size
            examples_per_sec = num_examples_per_step / duration
            sec_per_batch = float(duration)

            format_str = ('%s: step %d, loss = %.2f (%.1f examples/sec; %.3f '
                          'sec/batch)')
            print (format_str % (datetime.now(), step, loss_value,
                                 examples_per_sec, sec_per_batch))

          if step % FLAGS.period_evaluate == 0:
            prec_train = evaluate_set (sess, predict_ops,      localized_tr, keep_prob)
            prec_eval  = evaluate_set (sess, predict_eval_ops, localized_ev, keep_prob)
            prec_test  = evaluate_set (sess, predict_test_ops, localized_te, keep_prob)
            print('%s: prec_train = %.3f' % (datetime.now(), prec_train))
            print('%s: prec_eval  = %.3f' % (datetime.now(), prec_eval))
            print('%s: prec_test  = %.3f' % (datetime.now(), prec_test))
            print('regr_train_val: \n', regr_train_val[:8])
            print('regr_loss_val: \n', regression_loss_val[:8])

          if step % FLAGS.period_summary == 0:
            summary_str = sess.run(summary_op, 
              feed_dict={summary_train_prec: prec_train,
                         summary_eval_prec:  prec_eval,
                         summary_test_prec:  prec_test,
                         keep_prob:          1.0})
            summary_writer.add_summary(summary_str, step)

          # Save the model checkpoint periodically.
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
  parser.add_argument('--train_dir',   default='log/tensorflow/classifier_train',
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
  parser.add_argument('--train_list_name', default='train_list.txt')
  parser.add_argument('--eval_list_name',  default='eval_list.txt')
  parser.add_argument('--test_list_name',  default='test_list.txt')
  parser.add_argument('--batch_size', default=128, type=int,
                      help='Number of images to process in a batch.')
  # flags from citycam
  parser.add_argument('--data_dir', default='augmentation/patches',
                      help='Path to the citycam data directory.')
  # parameters from citycam
  parser.add_argument('--num_epochs_per_decay', default=350.0, type=float,
                      help='Epochs after which learning rate decays.')
  parser.add_argument('--learning_rate_decay_factor', default=0.1, type=float)
  parser.add_argument('--initial_learning_rate_decay', default=0.1, type=float)
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
  tf.app.flags.DEFINE_string('train_list_name', args.train_list_name, '')
  tf.app.flags.DEFINE_string('eval_list_name',  args.eval_list_name, '')
  tf.app.flags.DEFINE_string('test_list_name',  args.test_list_name, '')
  tf.app.flags.DEFINE_string('train_dir', atcity(args.train_dir), '')
  tf.app.flags.DEFINE_string('restore_from_dir', atcity(args.restore_from_dir), '')
  tf.app.flags.DEFINE_integer('max_steps', args.max_steps, '')
  tf.app.flags.DEFINE_integer('num_eval_examples', args.num_eval_examples, '')
  tf.app.flags.DEFINE_integer('batch_size', args.batch_size, '')

  tf.app.flags.DEFINE_float('NUM_EPOCHS_PER_DECAY', args.num_epochs_per_decay, '')
  tf.app.flags.DEFINE_float('LEARNING_RATE_DECAY_FACTOR', 
                              args.learning_rate_decay_factor, '')
  tf.app.flags.DEFINE_float('INITIAL_LEARNING_RATE', 
                              args.initial_learning_rate_decay, '')
  tf.app.flags.DEFINE_integer('num_preprocess_threads', args.num_preprocess_threads, '')

  tf.app.run()
