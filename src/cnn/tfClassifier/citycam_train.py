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

FLAGS = tf.app.flags.FLAGS



def evaluate_set (sess, (correct_op, predicted_op, labels_op), num_examples):
  """Convenience function to run evaluation for for every batch. 
     Sum the number of correct predictions and output one precision value.
  Args:
    sess:      current Session
    top_k_op:  tensor of type tf.nn.in_top_k
  """
  num_iter = int(math.ceil(num_examples / FLAGS.batch_size))
  true_count = 0  # Counts the number of correct predictions.
  total_sample_count = num_iter * FLAGS.batch_size

  predicted_list = []
  labels_list    = []

  for step in xrange(num_iter):

    [correct, predicted, labels]  = sess.run([correct_op, predicted_op, labels_op])
    #print (correct)
    #print (predicted)
    #print (labels)

    true_count     += np.sum(correct)
    predicted_list += predicted.tolist()
    labels_list    += labels.tolist()

  print (confusion_matrix(np.array(predicted_list), np.array(labels_list)))

  # Compute precision
  return true_count / total_sample_count




def train():
  """Train citycam for a number of steps."""
  with tf.Graph().as_default():
    with tf.variable_scope("model") as scope:
        global_step = tf.Variable(0, trainable=False)

        # Get images and labels for citycam.
        images, labels           = citycam.distorted_inputs('train_list.txt')
        images_eval, labels_eval = citycam.distorted_inputs('train_eval_list.txt')
        images_test, labels_test = citycam.inputs('test_list.txt')

        # Build a Graph that computes the logits predictions from the
        # inference model.
        logits      = citycam.inference(images)
        scope.reuse_variables()
        logits_eval = citycam.inference(images_eval)
        logits_test = citycam.inference(images_test)

        # Calculate loss.
        loss = citycam.loss(logits, labels)

        # Visualize conv1 features
        with tf.variable_scope('conv1') as scope_conv:
          weights = tf.get_variable('weights')
          grid = citycam.put_kernels_on_grid (weights, (8, 8))
          tf.image_summary('conv1/features', grid, max_images=1)

        predict_ops      = citycam.predict(logits,      labels)
        predict_eval_ops = citycam.predict(logits_eval, labels_eval)
        predict_test_ops = citycam.predict(logits_test, labels_test)

        summary_train_prec = tf.placeholder(tf.float32)
        summary_eval_prec  = tf.placeholder(tf.float32)
        summary_test_prec  = tf.placeholder(tf.float32)
        tf.scalar_summary('precision/train.', summary_train_prec)
        tf.scalar_summary('precision/eval.', summary_eval_prec)
        tf.scalar_summary('precision/test.', summary_test_prec)

        # Build a Graph that trains the model with one batch of examples and
        # updates the model parameters.
        train_op = citycam.train(loss, global_step)

        # Create a saver.
        saver = tf.train.Saver(tf.all_variables())

        # Build the summary operation based on the TF collection of Summaries.
        summary_op = tf.merge_all_summaries()

        # Build an initialization operation to run below.
        init = tf.initialize_all_variables()

        # Start running operations on the Graph.
        sess = tf.Session(config=tf.ConfigProto(
            log_device_placement=FLAGS.log_device_placement))
        sess.run(init)

        summary_writer = tf.train.SummaryWriter(FLAGS.train_dir,
                                                graph_def=sess.graph_def)

        # Start the queue runners.
        coord = tf.train.Coordinator()
        threads = tf.train.start_queue_runners(sess=sess, coord=coord)

        with coord.stop_on_exception():
          for step in xrange(FLAGS.max_steps):
            if coord.should_stop(): 
              break

            start_time = time.time()
            _, loss_value = sess.run([train_op, loss])
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
              prec_train = evaluate_set (sess, predict_ops,      FLAGS.num_eval_examples)
              prec_eval  = evaluate_set (sess, predict_eval_ops, FLAGS.num_eval_examples)
              prec_test  = evaluate_set (sess, predict_test_ops, FLAGS.num_eval_examples)
              print('%s: prec_train = %.3f' % (datetime.now(), prec_train))
              print('%s: prec_eval  = %.3f' % (datetime.now(), prec_eval))
              print('%s: prec_test  = %.3f' % (datetime.now(), prec_test))

            if step % FLAGS.period_summary == 0:
              summary_str = sess.run(summary_op, 
                feed_dict={summary_train_prec: prec_train,
                           summary_eval_prec: prec_eval,
                           summary_test_prec: prec_test})
              summary_writer.add_summary(summary_str, step)

            # Save the model checkpoint periodically.
            if step % FLAGS.period_checkpoint == 0 or (step + 1) == FLAGS.max_steps:
              checkpoint_path = os.path.join(FLAGS.train_dir, 'model.ckpt')
              saver.save(sess, checkpoint_path, global_step=step)

        coord.request_stop()
        coord.join(threads, stop_grace_period_secs=10)



def main(argv=None):  # pylint: disable=unused-argument
  if tf.gfile.Exists(FLAGS.train_dir):
    tf.gfile.DeleteRecursively(FLAGS.train_dir)
  tf.gfile.MakeDirs(FLAGS.train_dir)
  train()


if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  parser.add_argument('--train_dir', default='log/tensorflow/classifier_train',
                      help='Directory where to write event logs and checkpoint.')
  parser.add_argument('--log_device_placement', action='store_true',
                      help='Whether to log device placement.')
  parser.add_argument('--max_steps', default=1000, type=int,
                      help='Number of batches to run.')
  parser.add_argument('--num_eval_examples', default=128, type=int,
                      help='Number of examples for evaluation')
  parser.add_argument('--period_print', default=10, type=int)
  parser.add_argument('--period_summary', default=100, type=int)
  parser.add_argument('--period_evaluate', default=100, type=int)
  parser.add_argument('--period_checkpoint', default=1000, type=int)
  # flags from citycam
  parser.add_argument('--data_dir', default='augmentation/patches',
                      help='Path to the citycam data directory.')
  parser.add_argument('--batch_size', default=128, type=int,
                      help='Number of images to process in a batch.')
  # parameters from citycam
  parser.add_argument('--num_epochs_per_decay', default=350.0, type=float,
                      help='Epochs after which learning rate decays.')
  parser.add_argument('--learning_rate_decay_factor', default=0.1, type=float)
  parser.add_argument('--initial_learning_rate_decay', default=0.1, type=float)
  parser.add_argument('--num_preprocess_threads', default=16, type=int)

  args = parser.parse_args()


  def atcity(x):
    return os.path.join(os.getenv('CITY_PATH'), x)
  def atcitydata(x):
    return os.path.join(os.getenv('CITY_DATA_PATH'), x)

  tf.app.flags.DEFINE_string('train_dir', atcity(args.train_dir), '')
  tf.app.flags.DEFINE_integer('max_steps', args.max_steps, '')
  tf.app.flags.DEFINE_integer('period_print', args.period_print, '')
  tf.app.flags.DEFINE_integer('period_summary', args.period_summary, '')
  tf.app.flags.DEFINE_integer('period_evaluate', args.period_summary, '')
  tf.app.flags.DEFINE_integer('period_checkpoint', args.period_checkpoint, '')
  tf.app.flags.DEFINE_integer('num_eval_examples', args.num_eval_examples, '')
  tf.app.flags.DEFINE_boolean('log_device_placement', args.log_device_placement, '')

  tf.app.flags.DEFINE_string('data_dir', atcitydata(args.data_dir), '')
  tf.app.flags.DEFINE_integer('batch_size', args.batch_size, '')

  tf.app.flags.DEFINE_float('NUM_EPOCHS_PER_DECAY', args.num_epochs_per_decay, '')
  tf.app.flags.DEFINE_float('LEARNING_RATE_DECAY_FACTOR', 
                              args.learning_rate_decay_factor, '')
  tf.app.flags.DEFINE_float('INITIAL_LEARNING_RATE', 
                              args.initial_learning_rate_decay, '')
  tf.app.flags.DEFINE_integer('num_preprocess_threads', args.num_preprocess_threads, '')

  tf.app.run()
