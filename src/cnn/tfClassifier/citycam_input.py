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
IN_IMAGE_WIDTH = 72
IN_IMAGE_HEIGHT = 72

# Dimensions that CNN trains for
IMAGE_WIDTH = 64
IMAGE_HEIGHT = 64
NUM_CHANNELS = 3
NUM_CLASSES = 2
NUM_EXAMPLES_PER_EPOCH_FOR_TRAIN = 1024
NUM_EXAMPLES_PER_EPOCH_FOR_EVAL = 1024

FLAGS = tf.app.flags.FLAGS



def read_my_file_format(filename_and_label, width, height):
  """Consumes a single image, bbox and label as a ' '-delimited string.

  Args:
    filename_and_label: A scalar string tensor.
        Filenames in filename_and_label are relative to FLAGS.data_dir

  Returns:
    Two tensors: the decoded image, and the string label.
  """
  # read a line of imagefile and label from the list
  record = tf.decode_csv(filename_and_label, [['']]*7, ' ')
  imagename = record[0] + tf.constant('.jpg')
  label_str = record[1]
  roi0_str, roi1_str, roi2_str, roi3_str = record[2:6]
  maskname  = record[6] + tf.constant('.png')

  # open and read imagefile
  _dir = tf.constant(op.join(os.getenv('CITY_DATA_PATH'), FLAGS.data_dir) + '/')
  imagepath = _dir + imagename
  image_contents = tf.read_file(imagepath)
  image = tf.image.decode_jpeg(image_contents)
  image.set_shape([height, width, NUM_CHANNELS])

  # process label
  label = tf.string_to_number(label_str, out_type=tf.int32)

  # process roi
  roi0 = tf.string_to_number(roi0_str, out_type=tf.float32) / IMAGE_HEIGHT
  roi1 = tf.string_to_number(roi1_str, out_type=tf.float32) / IMAGE_WIDTH
  roi2 = tf.string_to_number(roi2_str, out_type=tf.float32) / IMAGE_HEIGHT
  roi3 = tf.string_to_number(roi3_str, out_type=tf.float32) / IMAGE_WIDTH
  roi = tf.expand_dims(tf.pack([roi0, roi1, roi2, roi3]), 0)

  # open and read maskfile
  _dir = tf.constant(op.join(os.getenv('CITY_DATA_PATH'), FLAGS.data_dir) + '/')
  maskpath = _dir + maskname
  mask_contents = tf.read_file(maskpath)
  mask = tf.image.decode_png(mask_contents)
  mask.set_shape([height, width, 1])

  return image, label, roi, mask



def _generate_image_and_label_batch(image, label, roi, mask, min_queue_examples,
                                    batch_size, dataset_tag=''):
  """Construct a queued batch of images and labels.

  Args:
    image: 3-D Tensor of [height, width, 3] of type.float32.
    label: 1-D Tensor of type.int32
    min_queue_examples: int32, minimum number of samples to retain
      in the queue that provides of batches of examples.
    batch_size: Number of images per batch.

  Returns:
    images: 4D tensor of [batch_size, height, width, 3] size.
    labels: 1D tensor of [batch_size] size.
  """
  # Scale mask to [img_min, img_max]
  img_min = tf.reduce_min(image)
  img_max = tf.reduce_max(image)
  mask_disp = tf.to_float(mask) / 255 * (img_max - img_min) + img_min

  # Create a queue that shuffles the examples, and then
  # read 'batch_size' images + labels from the example queue.
  images, label_batch, rois, masks, masks_disp = tf.train.shuffle_batch(
      [image, label, roi, mask, mask_disp],
      batch_size=batch_size,
      num_threads=FLAGS.num_preprocess_threads,
      capacity=min_queue_examples + 3 * batch_size,
      min_after_dequeue=min_queue_examples)

  # Display the images in the visualizer.
  masks_disp  = tf.image.grayscale_to_rgb(tf.expand_dims(masks_disp, dim=-1))
  images_disp = tf.image.draw_bounding_boxes(images, rois)
  images_disp = tf.concat(2, [images_disp, masks_disp])
  tf.image_summary('images' + dataset_tag, images_disp, max_images=3)

  print ('shape of images batch: %s' % str(images.get_shape()))
  print ('shape of masks batch:  %s' % str(masks.get_shape()))
  print ('shape of rois batch:   %s' % str(rois.get_shape()))

  return images, tf.reshape(label_batch, [batch_size])



def distorted_inputs(data_list_path, batch_size, dataset_tag=''):
  """Construct distorted input for CIFAR training using the Reader ops.

    Returns:
      images: 4D tensor of 
                 [batch_size, IN_IMAGE_WIDTH, IN_IMAGE_HEIGHT, NUM_CHANNELS] size.
      labels: 1D tensor of [batch_size] size.
  """
  with open(data_list_path) as f:
    file_label_pairs = f.read().splitlines() 

  # Create a queue that produces the filenames to read.
  filename_queue = tf.train.string_input_producer(file_label_pairs)

  # Read examples from files in the filename queue.
  uint8image, label, roi, mask = read_my_file_format(filename_queue.dequeue(),
                                              IN_IMAGE_WIDTH, IN_IMAGE_HEIGHT)

  width = IMAGE_WIDTH
  height = IMAGE_HEIGHT

  # Image processing for training the network. Note the many random
  # distortions applied to the image.

  # Prepare to crop and flip the image and the mask together
  rgba = tf.concat(2, [uint8image, mask])

  # Randomly crop a [height, width] section of the image.
  rgba = tf.random_crop(rgba, [height, width, 4])

  # Randomly flip the image horizontally.
  rgba = tf.image.random_flip_left_right(rgba)

  # Split back into image and mask
  cropped_image = tf.slice(rgba, begin=[0,0,0], size=[-1,-1,3])
  cropped_mask  = tf.slice(rgba, begin=[0,0,3], size=[-1,-1,1])
  cropped_mask  = tf.squeeze(cropped_mask, squeeze_dims=[2])

  cropped_image = tf.to_float(cropped_image)

  # Because these operations are not commutative, consider randomizing
  # randomize the order their operation.
  distorted_image = tf.image.random_brightness(cropped_image,
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
  return _generate_image_and_label_batch(float_image, label, roi, cropped_mask,
                                         min_queue_examples, batch_size, 
                                         dataset_tag)



def inputs(data_list_path, batch_size, dataset_tag=''):
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
  uint8image, label, roi, mask = read_my_file_format(filename_queue.dequeue(),
                                                    IMAGE_WIDTH, IMAGE_HEIGHT)
  reshaped_image = tf.to_float(uint8image)

  mask  = tf.squeeze(mask, squeeze_dims=[2])

  # Image processing for evaluation.
  # Crop the central [height, width] of the image.
#  resized_image = tf.image.resize_image_with_crop_or_pad(reshaped_image, 
#                                              IMAGE_WIDTH, IMAGE_HEIGHT)

  # Subtract off the mean and divide by the variance of the pixels.
  float_image = tf.image.per_image_whitening(reshaped_image)

  # Ensure that the random shuffling has good mixing properties.
  min_fraction_of_examples_in_queue = 0.4
  min_queue_examples = int(num_examples_per_epoch *
                           min_fraction_of_examples_in_queue)
  print ('Filling queue with %d citycam images before starting to train. '
         'This will take a few minutes.' % min_queue_examples)

  # Generate a batch of images and labels by building up a queue of examples.
  return _generate_image_and_label_batch(float_image, label, roi, mask,
                                         min_queue_examples, batch_size, 
                                         dataset_tag)
 
