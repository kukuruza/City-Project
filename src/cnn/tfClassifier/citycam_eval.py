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

"""Evaluation for citycam.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import datetime
import math
import time
import argparse
import os, os.path
import numpy as np
import tensorflow as tf

import citycam

FLAGS = tf.app.flags.FLAGS

# tf.app.flags.DEFINE_string('eval_dir',
#             os.path.join(os.getenv('CITY_PATH'), 'log/tensorflow/classifier_eval'
#                            """Directory where to write event logs.""")
# tf.app.flags.DEFINE_string('eval_data', 'train_eval',
#                            """Either 'test' or 'train_eval'.""")
# tf.app.flags.DEFINE_string('checkpoint_dir', 
#      os.path.join(os.getenv('CITY_PATH'), 'log/tensorflow/classifier_train'),
#                            """Directory where to read model checkpoints.""")
# tf.app.flags.DEFINE_integer('eval_interval_secs', 60 * 5,
#                             """How often to run the eval.""")
# tf.app.flags.DEFINE_integer('num_examples', 10000,
#                             """Number of examples to run.""")
# tf.app.flags.DEFINE_boolean('run_once', True,
#                          """Whether to run eval only once.""")


def eval_once(saver, summary_writer, top_k_op, summary_op):
  """Run Eval once.

  Args:
    saver: Saver.
    summary_writer: Summary writer.
    top_k_op: Top K op.
    summary_op: Summary op.
  """
  with tf.Session() as sess:
    ckpt = tf.train.get_checkpoint_state(FLAGS.checkpoint_dir)
    if ckpt and ckpt.model_checkpoint_path:
      # Restores from checkpoint
      saver.restore(sess, ckpt.model_checkpoint_path)
      # Assuming model_checkpoint_path looks something like:
      #   /my-favorite-path/citycam/model.ckpt-0,
      # extract global_step from it.
      global_step = ckpt.model_checkpoint_path.split('/')[-1].split('-')[-1]
    else:
      print('No checkpoint file found')
      return

    # Start the queue runners.
    coord = tf.train.Coordinator()
    try:
      threads = []
      for qr in tf.get_collection(tf.GraphKeys.QUEUE_RUNNERS):
        threads.extend(qr.create_threads(sess, coord=coord, daemon=True,
                                         start=True))

      num_iter = int(math.ceil(FLAGS.num_examples / FLAGS.batch_size))
      true_count = 0  # Counts the number of correct predictions.
      total_sample_count = num_iter * FLAGS.batch_size
      step = 0
      while step < num_iter and not coord.should_stop():
        predictions = sess.run([top_k_op])
        true_count += np.sum(predictions)
        step += 1

      # Compute precision @ 1.
      precision = true_count / total_sample_count
      print('%s: precision @ 1 = %.3f' % (datetime.now(), precision))

      summary = tf.Summary()
      summary.ParseFromString(sess.run(summary_op))
      summary.value.add(tag='Precision @ 1', simple_value=precision)
      summary_writer.add_summary(summary, global_step)
    except Exception as e:  # pylint: disable=broad-except
      coord.request_stop(e)

    coord.request_stop()
    coord.join(threads, stop_grace_period_secs=10)


def evaluate():
  """Eval citycam for a number of steps."""
  with tf.Graph().as_default():
    # Get images and labels for citycam.
    images, labels = citycam.inputs(FLAGS.data_list_name)

    # Build a Graph that computes the logits predictions from the inference model.
    with tf.variable_scope("inference") as scope:
      logits = citycam.inference(images)

    # Calculate predictions.
    top_k_op = tf.nn.in_top_k(logits, labels, 1)

    # Restore the moving average version of the learned variables for eval.
    variable_averages = tf.train.ExponentialMovingAverage(
        citycam.MOVING_AVERAGE_DECAY)
    variables_to_restore = variable_averages.variables_to_restore()
    saver = tf.train.Saver([v for v in tf.all_variables() if v.name.find('inference') >= 0])

    # Build the summary operation based on the TF collection of Summaries.
    summary_op = tf.merge_all_summaries()

    graph_def = tf.get_default_graph().as_graph_def()
    summary_writer = tf.train.SummaryWriter(FLAGS.eval_dir,
                                            graph_def=graph_def)

    while True:
      eval_once(saver, summary_writer, top_k_op, summary_op)
      if FLAGS.run_once:
        break
      time.sleep(FLAGS.eval_interval_secs)


def main(argv=None):  # pylint: disable=unused-argument
  if tf.gfile.Exists(FLAGS.eval_dir):
    tf.gfile.DeleteRecursively(FLAGS.eval_dir)
  tf.gfile.MakeDirs(FLAGS.eval_dir)
  evaluate()


if __name__ == '__main__':

  parser = argparse.ArgumentParser()
#  parser.add_argument('--data_dir', default='augmentation/patches',
#                      help='Path to the citycam data directory.')
  parser.add_argument('--eval_dir', default='log/tensorflow/classifier_eval',
                      help='Directory where to write event logs.')
  parser.add_argument('--train_eval', action='store_true',
                      help='Either "test" (default) or "train_eval".')
  parser.add_argument('--restore_from_dir', default='log/tensorflow/classifier_train',
                      help='Directory where to read model checkpoints.')
  parser.add_argument('--eval_interval_secs', default=60*5, type=int,
                      help='How often to run the eval.')
  parser.add_argument('--num_examples', default=1000, type=int,
                      help='Whether to run eval only once.')
  parser.add_argument('--run_once', action='store_true',
                      help='Whether to run eval only once.')
  parser.add_argument('--num_preprocess_threads', default=16, type=int)

  args = parser.parse_args()


  def atcity(x):
    return os.path.join(os.getenv('CITY_PATH'), x)
  def atcitydata(x):
    return os.path.join(os.getenv('CITY_DATA_PATH'), x)

  tf.app.flags.DEFINE_string('data_dir', '/home/etoropov/projects/City-Project/data/augmentation/patches-100K', '')
  tf.app.flags.DEFINE_string('eval_dir', atcity(args.eval_dir), '')
  data_list_name = 'train_eval_list.txt' if args.train_eval else 'test_list.txt'
  tf.app.flags.DEFINE_string('data_list_name', data_list_name, '')
  tf.app.flags.DEFINE_string('checkpoint_dir', atcity(args.restore_from_dir), '')
  tf.app.flags.DEFINE_integer('eval_interval_secs', args.eval_interval_secs, '')
  tf.app.flags.DEFINE_integer('num_examples', args.num_examples, '')
  tf.app.flags.DEFINE_boolean('run_once', args.run_once, '')
  tf.app.flags.DEFINE_integer('num_preprocess_threads', args.num_preprocess_threads, '')

  print ('data_dir: %s' % FLAGS.data_dir)

  tf.app.run()
