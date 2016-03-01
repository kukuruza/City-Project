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

"""A binary to train binary citycam using a single GPU.

Accuracy:
citycam_train.py achieves ~86% accuracy after 100K steps (256 epochs of
data) as judged by citycam_eval.py.

Speed: With batch_size 128.

System        | Step Time (sec/batch)  |     Accuracy
------------------------------------------------------------------
1 Tesla K20m  | 0.35-0.60              | ~86% at 60K steps  (5 hours)
1 Tesla K40m  | 0.25-0.35              | ~86% at 100K steps (4 hours)

Usage:
Please see the tutorial and website for how to download the CIFAR-10
data set, compile the program and train the model.

http://tensorflow.org/tutorials/deep_cnn/
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import datetime
import os, os.path
import time
import argparse

import numpy as np
from six.moves import xrange  # pylint: disable=redefined-builtin
import tensorflow as tf

import citycam

FLAGS = tf.app.flags.FLAGS


def train():
  """Train citycam-2 for a number of steps."""
  with tf.Graph().as_default():
    global_step = tf.Variable(0, trainable=False)

    # Get images and labels for citycam.
    #images, labels = citycam.distorted_inputs()
    images, labels = citycam.inputs('train_list.txt')

    # Build a Graph that computes the logits predictions from the
    # inference model.
    logits = citycam.inference(images)

    # Calculate loss.
    loss = citycam.loss(logits, labels)

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

    # Start the queue runners.
    tf.train.start_queue_runners(sess=sess)

    summary_writer = tf.train.SummaryWriter(FLAGS.train_dir,
                                            graph_def=sess.graph_def)

    for step in xrange(FLAGS.max_steps):
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

      if step % FLAGS.period_summary == 0:
        summary_str = sess.run(summary_op)
        summary_writer.add_summary(summary_str, step)

      # Save the model checkpoint periodically.
      if step % FLAGS.period_checkpoint == 0 or (step + 1) == FLAGS.max_steps:
        checkpoint_path = os.path.join(FLAGS.train_dir, 'model.ckpt')
        saver.save(sess, checkpoint_path, global_step=step)


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
  parser.add_argument('--period_print', default=10, type=int)
  parser.add_argument('--period_summary', default=100, type=int)
  parser.add_argument('--period_checkpoint', default=1000, type=int)
  parser.add_argument('--max_steps', default=1000, type=int,
                      help='Whether to run eval only once.')
  args = parser.parse_args()


  def atcity(x):
    return os.path.join(os.getenv('CITY_PATH'), x)

  tf.app.flags.DEFINE_string('train_dir', atcity(args.train_dir), '')
  tf.app.flags.DEFINE_integer('max_steps', args.max_steps, '')
  tf.app.flags.DEFINE_integer('period_print', args.period_print, '')
  tf.app.flags.DEFINE_integer('period_summary', args.period_summary, '')
  tf.app.flags.DEFINE_integer('period_checkpoint', args.period_checkpoint, '')
  tf.app.flags.DEFINE_boolean('log_device_placement', args.log_device_placement, '')

  tf.app.run()
