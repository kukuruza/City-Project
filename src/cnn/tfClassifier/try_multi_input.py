"""Routine for decoding the CIFAR-10 binary file format."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os, os.path as op

import argparse
import numpy as np
import tensorflow as tf

FLAGS = tf.app.flags.FLAGS


# Dimensions of images stored in jpeg
IN_IMAGE_WIDTH = 80
IN_IMAGE_HEIGHT = 60
NUM_CHANNELS = 3



def read_my_file_format(filename_and_label):

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
  # Create a queue that shuffles the examples, and then
  # read 'batch_size' images + labels from the example queue.
  num_preprocess_threads = 16
  images, label_batch = tf.train.shuffle_batch(
      [image, label],
      batch_size=batch_size,
      num_threads=num_preprocess_threads,
      capacity=min_queue_examples + 3 * batch_size,
      min_after_dequeue=min_queue_examples)

  return images, tf.reshape(label_batch, [batch_size])



def inputs(data_list_name):

  data_dir = '/Users/evg/projects/City-Project/data/augmentation/patches'
  data_list_path = op.join(data_dir, data_list_name)

  with open(data_list_path) as f:
    file_label_pairs = f.read().splitlines() 

  # Create a queue that produces the filenames to read.
  filename_queue = tf.train.string_input_producer(file_label_pairs)

  # Read example and label from files in the filename queue.
  uint8image, label = read_my_file_format(filename_queue.dequeue())
  reshaped_image = tf.to_float(uint8image)

  width = 80
  height = 60

  # Image processing for evaluation.
  # Crop the central [height, width] of the image.
  resized_image = tf.image.resize_image_with_crop_or_pad(reshaped_image, 
                                                         width, height)

  # Subtract off the mean and divide by the variance of the pixels.
  float_image = tf.image.per_image_whitening(resized_image)

  # Ensure that the random shuffling has good mixing properties.
  min_queue_examples = FLAGS.batch_size
  print ('Filling queue with %d citycam images before starting to train. '
         'This will take a few minutes.' % min_queue_examples)

  # Generate a batch of images and labels by building up a queue of examples.
  return _generate_image_and_label_batch(float_image, label,
                                         min_queue_examples, FLAGS.batch_size)



def evaluate():
 
  with tf.variable_scope("myscope") as scope:

    images_op1, labels_op1 = inputs('train_eval_list.txt')
    #scope.reuse_variables()
    images_op2, labels_op2 = inputs('test_list.txt')

    with tf.Session() as sess:
      coord = tf.train.Coordinator()
      threads = tf.train.start_queue_runners(sess=sess, coord=coord)
      with coord.stop_on_exception():
        while not coord.should_stop():

          result = sess.run([images_op1, labels_op1])
          print (result[1])
          result = sess.run([images_op2, labels_op2])
          print (result[1])

      coord.request_stop()
      coord.join(threads, stop_grace_period_secs=10)



if __name__ == '__main__':

  def atcitydata(x):
    return op.join(os.getenv('CITY_DATA_PATH'), x)

  tf.app.flags.DEFINE_string('data_dir', atcitydata('augmentation/patches'), '')
  tf.app.flags.DEFINE_integer('batch_size', 128, '')

  evaluate()
