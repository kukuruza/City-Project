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


# Dimensions of images stored in jpeg
IN_IMAGE_WIDTH = 80
IN_IMAGE_HEIGHT = 60

# Dimensions that CNN trains for
IMAGE_WIDTH = 80
IMAGE_HEIGHT = 60
NUM_CHANNELS = 3
NUM_CLASSES = 2
NUM_EXAMPLES_PER_EPOCH_FOR_TRAIN = 5000
NUM_EXAMPLES_PER_EPOCH_FOR_EVAL = 1000



def read_my_file_format(filename_and_label):
  """Consumes a single filename and label as a ' '-delimited string.

  Args:
    filename_and_label: A scalar string tensor.

  Returns:
    Two tensors: the decoded image, and the string label.
  """
  # read a line of imagefile and label from the list
  filename, label_str = tf.decode_csv(filename_and_label, [[""], [""]], " ")

  # open and read that imagefile
  filepath = tf.constant(os.getenv('CITY_DATA_PATH') + '/') + filename
  file_contents = tf.read_file( filepath )
  example = tf.image.decode_jpeg(file_contents)
  example.set_shape([IN_IMAGE_HEIGHT, IN_IMAGE_WIDTH, NUM_CHANNELS])

  # process label
  label = tf.string_to_number(label_str, out_type=tf.int32)

  return example, label



def _generate_image_and_label_batch(image, label, min_queue_examples,
                                    batch_size):
  """Construct a queued batch of images and labels.

  Args:
    image: 3-D Tensor of [height, width, 3] of type.float32.
    label: 1-D Tensor of type.int32
    min_queue_examples: int32, minimum number of samples to retain
      in the queue that provides of batches of examples.
    batch_size: Number of images per batch.

  Returns:
    images: Images. 4D tensor of [batch_size, height, width, 3] size.
    labels: Labels. 1D tensor of [batch_size] size.
  """
  # Create a queue that shuffles the examples, and then
  # read 'batch_size' images + labels from the example queue.
  num_preprocess_threads = 16
  images, label_batch = tf.train.shuffle_batch(
      [image, label],
      batch_size=batch_size,
      num_threads=num_preprocess_threads,
      capacity=min_queue_examples + 3 * batch_size,
      min_after_dequeue=min_queue_examples)

  # Display the training images in the visualizer.
  tf.image_summary('images', images)

  return images, tf.reshape(label_batch, [batch_size])



def distorted_inputs(data_list_path, batch_size):
  """Construct distorted input for CIFAR training using the Reader ops.

    Returns:
      images: Images. 4D tensor of 
                 [batch_size, IMAGE_HEIGHT, IMAGE_WIDTH, NUM_CHANNELS] size.
      labels: Labels. 1D tensor of [batch_size] size.
  """
  with open(data_list_path) as f:
    file_label_pairs = f.read().splitlines() 

  # Create a queue that produces the filenames to read.
  filename_queue = tf.train.string_input_producer(file_label_pairs)

  # Read examples from files in the filename queue.
  uint8image, label = read_my_file_format(filename_queue.dequeue())
  reshaped_image = tf.to_float(uint8image)

  width = IMAGE_WIDTH
  height = IMAGE_HEIGHT

  # Image processing for training the network. Note the many random
  # distortions applied to the image.

  # Randomly crop a [height, width] section of the image.
  distorted_image = tf.random_crop(reshaped_image, [height, width, 3])

  # Randomly flip the image horizontally.
  distorted_image = tf.image.random_flip_left_right(distorted_image)

  # Because these operations are not commutative, consider randomizing
  # randomize the order their operation.
  distorted_image = tf.image.random_brightness(distorted_image,
                                               max_delta=63)
  distorted_image = tf.image.random_contrast(distorted_image,
                                             lower=0.2, upper=1.8)

  # Subtract off the mean and divide by the variance of the pixels.
  float_image = tf.image.per_image_whitening(distorted_image)

  # Ensure that the random shuffling has good mixing properties.
  min_fraction_of_examples_in_queue = 0.4
  min_queue_examples = int(NUM_EXAMPLES_PER_EPOCH_FOR_TRAIN *
                           min_fraction_of_examples_in_queue)
  print ('Filling queue with %d citycam images before starting to train. '
         'This will take a few minutes.' % min_queue_examples)

  # Generate a batch of images and labels by building up a queue of examples.
  return _generate_image_and_label_batch(float_image, label,
                                         min_queue_examples, batch_size)



def inputs(data_list_path, batch_size):
  """
    Returns:
      images: Images. 4D tensor of 
                 [batch_size, IMAGE_HEIGHT, IMAGE_WIDTH, NUM_CHANNELS] size.
      labels: Labels. 1D tensor of [batch_size] size.
  """
  if op.basename(data_list_path) == 'test_list.txt':
    num_examples_per_epoch = NUM_EXAMPLES_PER_EPOCH_FOR_EVAL
  else:
    num_examples_per_epoch = NUM_EXAMPLES_PER_EPOCH_FOR_TRAIN

  with open(data_list_path) as f:
    file_label_pairs = f.read().splitlines() 

  # Create a queue that produces the filenames to read.
  filename_queue = tf.train.string_input_producer(file_label_pairs)

  # Read example and label from files in the filename queue.
  uint8image, label = read_my_file_format(filename_queue.dequeue())
  reshaped_image = tf.to_float(uint8image)

  width = IMAGE_WIDTH
  height = IMAGE_HEIGHT

  # Image processing for evaluation.
  # Crop the central [height, width] of the image.
  resized_image = tf.image.resize_image_with_crop_or_pad(reshaped_image, 
                                                         width, height)

  # Subtract off the mean and divide by the variance of the pixels.
  float_image = tf.image.per_image_whitening(resized_image)

  # Ensure that the random shuffling has good mixing properties.
  min_fraction_of_examples_in_queue = 0.4
  min_queue_examples = int(num_examples_per_epoch *
                           min_fraction_of_examples_in_queue)
  print ('Filling queue with %d citycam images before starting to train. '
         'This will take a few minutes.' % min_queue_examples)

  # Generate a batch of images and labels by building up a queue of examples.
  return _generate_image_and_label_batch(float_image, label,
                                         min_queue_examples, batch_size)

  # min_after_dequeue defines how big a buffer we will randomly sample
  #   from -- bigger means better shuffling but slower start up and more
  #   memory used.
  # capacity must be larger than min_after_dequeue and the amount larger
  #   determines the maximum we will prefetch.  Recommendation:
  #   min_after_dequeue + (num_threads + a small safety margin) * batch_size
  # min_after_dequeue = 1000
  # capacity = min_after_dequeue + 3 * batch_size
  # example_batch, label_batch = tf.train.shuffle_batch(
  #     [example, label], batch_size=batch_size, capacity=capacity,
  #     min_after_dequeue=min_after_dequeue)
  # return example_batch, label_batch
