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

"""Routine for decoding the CIFAR-10 binary file format."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os, os.path as op

from six.moves import xrange  # pylint: disable=redefined-builtin
import tensorflow as tf


# Global constants describing the CIFAR-10 data set.
IMAGE_WIDTH = 80
IMAGE_HEIGHT = 60
NUM_CHANNELS = 3
NUM_CLASSES = 2
NUM_EXAMPLES_PER_EPOCH_FOR_TRAIN = 50000
NUM_EXAMPLES_PER_EPOCH_FOR_EVAL = 10000



def read_my_file_format(filename_and_label):
  """Consumes a single filename and label as a ' '-delimited string.

  Args:
    filename_and_label: A scalar string tensor.

  Returns:
    Two tensors: the decoded image, and the string label.
  """
  filename, label_str = tf.decode_csv(filename_and_label, [[""], [""]], " ")
  filepath = tf.constant(os.getenv('CITY_DATA_PATH') + '/') + filename
  file_contents = tf.read_file( filepath )
  example = tf.image.decode_jpeg(file_contents)
  label = tf.string_to_number(label_str, out_type=tf.int32)
  return tf.image.per_image_whitening(tf.to_float(example)), label


def inputs(data_list_path, batch_size):
  """
    Returns:
      images: Images. 4D tensor of 
                 [batch_size, IMAGE_HEIGHT, IMAGE_WIDTH, NUM_CHANNELS] size.
      labels: Labels. 1D tensor of [batch_size] size.
  """
  with open(data_list_path) as f:
    file_label_pairs = f.read().splitlines() 

  filename_queue = tf.train.string_input_producer(file_label_pairs)
  example, label = read_my_file_format(filename_queue.dequeue())
  example.set_shape([IMAGE_HEIGHT, IMAGE_WIDTH, NUM_CHANNELS])
  # min_after_dequeue defines how big a buffer we will randomly sample
  #   from -- bigger means better shuffling but slower start up and more
  #   memory used.
  # capacity must be larger than min_after_dequeue and the amount larger
  #   determines the maximum we will prefetch.  Recommendation:
  #   min_after_dequeue + (num_threads + a small safety margin) * batch_size
  min_after_dequeue = 1000
  capacity = min_after_dequeue + 3 * batch_size
  example_batch, label_batch = tf.train.shuffle_batch(
      [example, label], batch_size=batch_size, capacity=capacity,
      min_after_dequeue=min_after_dequeue)
  return example_batch, label_batch
