from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os, os.path as op
import re
import sys
import tarfile
from math import sqrt

import tensorflow as tf

import citycam_input


FLAGS = tf.app.flags.FLAGS

# Basic model parameters. UPDATE: set in main()
#tf.app.flags.DEFINE_integer('batch_size', 128,
#                            """Number of images to process in a batch.""")
# tf.app.flags.DEFINE_string('data_dir', 
#               op.join(os.getenv('CITY_DATA_PATH'), 'augmentation/patches'),
#                            """Path to the citycam data directory.""")


# Global constants describing the citycam data set.
IMAGE_WIDTH  = citycam_input.IMAGE_WIDTH
IMAGE_HEIGHT = citycam_input.IMAGE_HEIGHT
NUM_CLASSES  = citycam_input.NUM_CLASSES
NUM_EXAMPLES_PER_EPOCH_FOR_TRAIN = citycam_input.NUM_EXAMPLES_PER_EPOCH_FOR_TRAIN
NUM_EXAMPLES_PER_EPOCH_FOR_EVAL  = citycam_input.NUM_EXAMPLES_PER_EPOCH_FOR_EVAL


# Constants describing the training process.
MOVING_AVERAGE_DECAY = 0.9999     # The decay to use for the moving average.
NUM_EPOCHS_PER_DECAY = 1      # Epochs after which learning rate decays.
LEARNING_RATE_DECAY_FACTOR = 0.9  # Learning rate decay factor.
INITIAL_LEARNING_RATE = 0.025       # Initial learning rate.

# If a model is trained with multiple GPU's prefix all Op names with tower_name
# to differentiate the operations. Note that this prefix is removed from the
# names of the summaries when visualizing a model.
TOWER_NAME = 'tower'

tf.app.flags.DEFINE_float('MOVING_AVERAGE_DECAY', MOVING_AVERAGE_DECAY, '')
tf.app.flags.DEFINE_float('NUM_EPOCHS_PER_DECAY', NUM_EPOCHS_PER_DECAY, 
                          """Epochs after which learning rate decays.""")
tf.app.flags.DEFINE_float('LEARNING_RATE_DECAY_FACTOR', LEARNING_RATE_DECAY_FACTOR, '')
tf.app.flags.DEFINE_float('INITIAL_LEARNING_RATE', INITIAL_LEARNING_RATE, '')

tf.app.flags.DEFINE_float('wd_conv', 0.005, 'weight_decay for all conv layers')
tf.app.flags.DEFINE_float('wd_fc',   0.005, 'weight_decay for all fc layers')
tf.app.flags.DEFINE_float('lambda_regr', 0.0, '')


def _activation_summary(x):
  """Helper to create summaries for activations.

  Creates a summary that provides a histogram of activations.
  Creates a summary that measure the sparsity of activations.

  Args:
    x: Tensor
  Returns:
    nothing
  """
  # Remove 'tower_[0-9]/' from the name in case this is a multi-GPU training
  # session. This helps the clarity of presentation on tensorboard.
  tensor_name = re.sub('%s_[0-9]*/' % TOWER_NAME, '', x.op.name)
  tf.histogram_summary(tensor_name + '/activations', x)
  tf.scalar_summary(tensor_name + '/sparsity', tf.nn.zero_fraction(x))


def _variable_with_weight_decay(name, shape, stddev, wd):
  """Helper to create an initialized Variable with weight decay.

  Note that the Variable is initialized with a truncated normal distribution.
  A weight decay is added only if one is specified.

  Args:
    name: name of the variable
    shape: list of ints
    stddev: standard deviation of a truncated Gaussian
    wd: add L2Loss weight decay multiplied by this float. If None, weight
        decay is not added for this Variable.

  Returns:
    Variable Tensor
  """
  var = tf.get_variable(name, shape,
                 initializer=tf.truncated_normal_initializer(stddev=stddev))
  if wd:
    weight_decay = tf.mul(tf.nn.l2_loss(var), wd, name='weight_loss')
    tf.add_to_collection('losses', weight_decay)
  return var


def distorted_inputs (data_list_name):
  """Construct distorted input for CIFAR training using the Reader ops.

  Returns:
    images: Images. 4D tensor of 
               [batch_size, IMAGE_HEIGHT, IMAGE_WIDTH, 3] size.
    labels: Labels. 1D tensor of [batch_size] size.

  Raises:
    ValueError: If no data_dir
  """
  if not FLAGS.data_dir:
    raise ValueError('Please supply a data_dir')
  train_list_path = os.path.join(FLAGS.data_dir, data_list_name)
  return citycam_input.distorted_inputs(train_list_path, FLAGS.batch_size)


def inputs (data_list_name):
  """Construct input for CIFAR evaluation using the Reader ops.

  Returns:
    images: Images. 4D tensor of 
               [batch_size, IMAGE_HEIGHT, IMAGE_WIDTH, 3] size.
    labels: Labels. 1D tensor of [batch_size] size.

  Raises:
    ValueError: If no data_dir
  """
  if not FLAGS.data_dir:
    raise ValueError('Please supply a data_dir')
  data_list_path = os.path.join(FLAGS.data_dir, data_list_name)
  return citycam_input.inputs(data_list_path, FLAGS.batch_size)




def put_kernels_on_grid (kernel, pad=1):
  '''Visualize conv. features as an image (mostly for the 1st layer).
  Place kernel into a grid, with some paddings between adjacent filters.

  Args:
    kernel:            tensor of shape [Y, X, NumChannels, NumKernels]
    (grid_Y, grid_X):  shape of the grid. Require: NumKernels == grid_Y * grid_X
                         User is responsible of how to break into two multiples.
    pad:               number of black pixels around each filter (between them)
  
  Return:
    Tensor of shape [(Y+pad)*grid_Y, (X+pad)*grid_X, NumChannels, 1],
      where NumKernels == grid_Y * grid_X
  '''
  NumChannels = kernel.get_shape()[2].value

  # shape of the grid. Require: NumKernels == grid_Y * grid_X
  def factorization(n):
    assert isinstance(n, ( int, long ))
    for i in range(int(sqrt(float(n))), 0, -1):
      if n % i == 0:
        if i == 1: print('Who would put a prime number of filters')
        return (int(i), int(n / i))
  (grid_Y, grid_X) = factorization (kernel.get_shape()[3].value)
  print ('(grid_Y, grid_X): %s' % str((grid_Y, grid_X)))

  # scale to [0, 1]
  x_min = tf.reduce_min(kernel)
  x_max = tf.reduce_max(kernel)
  x_0to1 = (kernel - x_min) / (x_max - x_min)

  # scale to [0, 255] and convert to uint8
  x_0to255_uint8 = tf.image.convert_image_dtype(x_0to1, dtype=tf.uint8)

  # pad X and Y
  x1 = tf.pad(x_0to255_uint8, tf.constant( [[pad,0],[pad,0],[0,0],[0,0]] ))

  # X and Y dimensions, w.r.t. padding
  Y = kernel.get_shape()[0] + pad
  X = kernel.get_shape()[1] + pad

  # put NumKernels to the 1st dimension
  x2 = tf.transpose(x1, (3, 0, 1, 2))
  # organize grid on Y axis
  x3 = tf.reshape(x2, tf.pack([grid_X, Y * grid_Y, X, NumChannels]))
  
  # switch X and Y axes
  x4 = tf.transpose(x3, (0, 2, 1, 3))
  # organize grid on X axis
  x5 = tf.reshape(x4, tf.pack([1, X * grid_X, Y * grid_Y, NumChannels]))
  
  # back to normal order (not combining with the next step for clarity)
  x6 = tf.transpose(x5, (2, 1, 3, 0))

  # to tf.image_summary order [batch_size, height, width, channels],
  #   where in this case batch_size == 1
  return tf.transpose(x6, (3, 0, 1, 2))



def demo_visualize_kernels(kernel):
  '''Send a kernel to image_summary
  Args
    kernel:   tensor of shape [Y, X, num_channels, num_filters]
  Returns
    the same kernel scaled and reshaped for expected image_summary input
  '''
  # scale weights to [0 255] and convert to uint8 (maybe change scaling?)
  x_min = tf.reduce_min(kernel)
  x_max = tf.reduce_max(kernel)
  kernel_0_to_1 = (kernel - x_min) / (x_max - x_min)
  # to tf.image_summary format [batch_size, height, width, channels]
  return tf.transpose (kernel_0_to_1, [3, 0, 1, 2])



def my_image_summary (images, masks, rois, setname):

  # Display the images in the visualizer.
  rois = tf.expand_dims(rois, 1)  # from [batch_size,4] to [batch_size,1,4]
  masks_disp  = tf.to_float(masks) / 255
  masks_disp  = tf.image.grayscale_to_rgb(tf.expand_dims(masks_disp, dim=-1))
  masks_wroi  = tf.image.draw_bounding_boxes(masks_disp, rois)
  images_wroi = tf.image.draw_bounding_boxes(images, rois)
  grid = tf.concat(1, [tf.concat(2, [images, images_wroi]),
                       tf.concat(2, [masks_disp, masks_wroi])])
  grid = tf.pad(grid, [[0,0],[4,4],[4,4],[0,0]])

  #   regress_disp = tf.expand_dims(regress[sn], 1)  # from [batch_size,4] to [batch_size,1,4]
  #   images_disp = tf.image.draw_bounding_boxes(images_disp, regr_tr_disp / 2)

  tf.image_summary('images/%s' % op.splitext(setname)[0], grid, max_images=3)





def L1_smooth(x):
  return tf.select (tf.greater(x, 1.0), tf.abs(x)-0.5, 0.5*tf.square(x))



def make_conv(input_, name, shape, padding, wd, stddev=0.01):
  with tf.variable_scope(name) as scope:
    kernel = _variable_with_weight_decay('weights', shape=shape, stddev=stddev, wd=wd)
    conv = tf.nn.conv2d(input_, kernel, [1, 1, 1, 1], padding=padding)
    biases = tf.get_variable('biases', [shape[3]], initializer=tf.constant_initializer(0.0))
    bias = tf.nn.bias_add(conv, biases)
    conv_layer = tf.nn.relu(bias, name=scope.name)
    _activation_summary(conv_layer)
  return conv_layer

def make_norm(input_, name):
  return tf.nn.lrn(input_, 4, bias=1.0, alpha=0.001 / 9.0, beta=0.75, name=name)

def make_fc(input_, name, shape, wd, stddev=0.01, keep_prob=1.0):
  with tf.variable_scope(name) as scope:
    weights  = _variable_with_weight_decay('weights', shape=shape, stddev=stddev, wd=wd)
    biases   = tf.get_variable('biases', shape[1], initializer=tf.constant_initializer(0.0))
    fc_layer = tf.nn.relu(tf.matmul(input_, weights) + biases, name=scope.name)
    fc_layer = tf.nn.dropout(fc_layer, keep_prob)
    _activation_summary(fc_layer)
  return fc_layer

def make_softmax(input_, shape):
  with tf.variable_scope('softmax_linear') as scope:
    weights = _variable_with_weight_decay('weights', shape=shape, stddev=1.0/shape[0], wd=0.0)
    biases = tf.get_variable('biases', [shape[1]], initializer=tf.constant_initializer(0.0))
    softmax_linear = tf.add(tf.matmul(input_, weights), biases, name=scope.name)
    _activation_summary(softmax_linear)
  return softmax_linear

def make_regr(input_, shape):
  assert shape[1] == 4
  with tf.variable_scope('regression') as scope:
    weights = _variable_with_weight_decay('weights', shape=shape, stddev=1.0/shape[0], wd=0.0)
    biases = tf.get_variable('biases', [shape[1]], initializer=tf.random_uniform_initializer(0.0, 1.0))
    regressions = tf.add(tf.matmul(input_, weights), biases, name=scope.name)
  return regressions


def inference2 (images, keep_prob):
  assert images.get_shape()[1] == 61 and images.get_shape()[2] == 61, \
         'images shape: %s' % str(images.get_shape())

  conv1 = make_conv     (images, name='conv1', padding='SAME',  shape=[11, 11, 3, 64], wd=FLAGS.wd_conv)
  pool1 = tf.nn.max_pool(conv1,  name='pool1', padding='VALID', ksize=[1, 9, 9, 1], strides=[1, 5, 5, 1])
  norm1 = make_norm     (pool1,  name='norm1') 

  conv2 = make_conv     (norm1,  name='conv2', padding='SAME',  shape=[5, 5, 64, 64], wd=FLAGS.wd_conv)
  norm2 = make_norm     (conv2,  name='norm2')
  pool2 = tf.nn.max_pool(norm2,  name='pool2', padding='SAME',  ksize=[1, 3, 3, 1], strides=[1, 2, 2, 1])

  #dim = 1
  #for d in pool2.get_shape()[1:].as_list(): dim *= d
  dim = 64 * 6 * 6
  reshape = tf.reshape (pool2, [FLAGS.batch_size, dim])
  fc1 = make_fc (reshape, name='fc1', shape=[dim, 384], stddev=0.04, wd=FLAGS.wd_fc, keep_prob=keep_prob)
  fc2_clas = make_fc (fc1, name='fc2_clas', shape=[384, 192], stddev=0.04, wd=FLAGS.wd_fc, keep_prob=keep_prob)
  softmax = make_softmax(fc2_clas, shape=[192, NUM_CLASSES])

  fc2_regr = make_fc (fc1, name='fc2_regr', shape=[384, 192], stddev=0.04, wd=FLAGS.wd_fc, keep_prob=keep_prob)
  regressions = make_regr(fc2_regr, shape=[192, 4])

  # Each value is a tuple (layer, accum_padding, accum_stride, half_receptive_field)
  layers = {'conv1': (conv1, 0, 1, 5),     'pool1': (pool1, 4, 5, 5+4),
            'conv2': (conv2, 4, 5, 9+2*5), 'pool2': (pool2, 4, 5*2, 19+1)}
  return softmax, regressions, layers



def inference3 (images, keep_prob):
  assert images.get_shape()[1] == 61 and images.get_shape()[2] == 61, \
         'images shape: %s' % str(images.get_shape())

  conv1 = make_conv     (images, name='conv1', padding='SAME',  shape=[7, 7, 3, 64], wd=FLAGS.wd_conv)
  norm1 = make_norm     (conv1,  name='norm1') 
  conv2 = make_conv     (norm1,  name='conv2', padding='SAME',  shape=[5, 5, 64, 64], wd=FLAGS.wd_conv)
  pool2 = tf.nn.max_pool(conv2,  name='pool2', padding='VALID', ksize=[1, 9, 9, 1], strides=[1, 5, 5, 1])
  norm2 = make_norm     (pool2,  name='norm2') 

  conv3 = make_conv     (norm2,  name='conv3', padding='SAME',  shape=[5, 5, 64, 64], wd=FLAGS.wd_conv)
  norm3 = make_norm     (conv3,  name='norm3')
  pool3 = tf.nn.max_pool(norm3,  name='pool3', padding='SAME',  ksize=[1, 3, 3, 1], strides=[1, 2, 2, 1])

  #dim = 1
  #for d in pool2.get_shape()[1:].as_list(): dim *= d
  dim = 64 * 6 * 6
  reshape = tf.reshape (pool3, [FLAGS.batch_size, dim])
  fc1 = make_fc (reshape, name='fc1', shape=[dim, 384], stddev=0.04, wd=FLAGS.wd_fc, keep_prob=keep_prob)
  fc2_clas = make_fc (fc1, name='fc2_clas', shape=[384, 192], stddev=0.04, wd=FLAGS.wd_fc, keep_prob=keep_prob)
  softmax = make_softmax(fc2_clas, shape=[192, NUM_CLASSES])

  fc2_regr = make_fc (fc1, name='fc2_regr', shape=[384, 192], stddev=0.04, wd=FLAGS.wd_fc, keep_prob=keep_prob)
  regressions = make_regr(fc2_regr, shape=[192, 4])

  # Each value is a tuple (layer, accum_padding, accum_stride, half_receptive_field)
  layers = {'conv1': (conv1, 0, 1, 3),
            'conv2': (conv2, 0, 1, 5),    'pool2': (pool2, 4, 5, 5+4),
            'conv3': (conv3, 4, 5, 9+2*5), 'pool3': (pool3, 4, 5*2, 19+1)}
  return softmax, regressions, layers



def inference5 (images, keep_prob):
  assert images.get_shape()[1] == 61 and images.get_shape()[2] == 61, \
         'images shape: %s' % str(images.get_shape())

  conv1 = make_conv     (images, name='conv1', padding='SAME',  shape=[7, 7, 3, 32], wd=FLAGS.wd_conv)
  norm1 = make_norm     (conv1,  name='norm1') 
  conv2 = make_conv     (norm1,  name='conv2', padding='SAME',  shape=[3, 3, 32, 32], wd=FLAGS.wd_conv)
  norm2 = make_norm     (conv2,  name='norm2') 
  pool2 = tf.nn.max_pool(norm2,  name='pool2', padding='SAME', ksize=[1, 3, 3, 1], strides=[1, 2, 2, 1])
  # 31
  
  conv3 = make_conv     (pool2,  name='conv3', padding='SAME',  shape=[3, 3, 32, 64], wd=FLAGS.wd_conv)
  norm3 = make_norm     (conv3,  name='norm3') 
  pool3 = tf.nn.max_pool(norm3,  name='pool3', padding='SAME', ksize=[1, 3, 3, 1], strides=[1, 2, 2, 1])
  # 15
  conv4 = make_conv     (pool3,  name='conv4', padding='SAME',  shape=[3, 3, 64, 128], wd=FLAGS.wd_conv)
  norm4 = make_norm     (conv4,  name='norm4')

  conv5 = make_conv     (norm4,  name='conv5', padding='VALID',  shape=[3, 3, 128, 128], wd=FLAGS.wd_conv)
  norm5 = make_norm     (conv5,  name='norm5')
  # 13
  pool5 = tf.nn.max_pool(norm5,  name='pool5', padding='SAME',  ksize=[1, 3, 3, 1], strides=[1, 2, 2, 1])
  # 7

  #dim = 1
  #for d in pool2.get_shape()[1:].as_list(): dim *= d
  dim = 128 * 7 * 7
  reshape = tf.reshape (pool5, [FLAGS.batch_size, dim])
  fc1 = make_fc (reshape, name='fc1', shape=[dim, 384], stddev=0.04, wd=FLAGS.wd_fc, keep_prob=keep_prob)
  fc2_clas = make_fc (fc1, name='fc2_clas', shape=[384, 192], stddev=0.04, wd=FLAGS.wd_fc, keep_prob=keep_prob)
  softmax = make_softmax(fc2_clas, shape=[192, NUM_CLASSES])

  fc2_regr = make_fc (fc1, name='fc2_regr', shape=[384, 192], stddev=0.04, wd=FLAGS.wd_fc, keep_prob=keep_prob)
  regressions = make_regr(fc2_regr, shape=[192, 4])

  # Each value is a tuple (layer, accum_padding, accum_stride, half_receptive_field)
  layers = {'conv1': (conv1, 0, 1, 1),
            'conv2': (conv2, 0, 1, 1+1*1),  'pool2': (pool2, 0, 2, 2+1*1),
            'conv3': (conv3, 0, 2, 3+1*2),  'pool3': (pool3, 0, 2*2, 5+1*4),
            'conv4': (conv4, 0, 4, 9+1*4), 
            'conv5': (conv5, 0, 4, 13+1*4), 'pool5': (pool5, 0, 4*2, 17+1*4)}
  return softmax, regressions, layers



def inference(images, keep_prob):
    '''Thin proxy too pick the architecture'''
    return inference5 (images, keep_prob=keep_prob)


def loss_clas (logits, labels):
  """Add L2Loss to all the trainable variables.
  Add summary for for "Loss" and "Loss/avg".
  Args:
    logits:       Logits from inference().
    labels:       1D Tensor of type tf.int32, [batch_size]
                  Labels from distorted_inputs or inputs(). 
  Returns:
    Loss tensor of type float.
  """
  # Calculate the average cross entropy loss across the batch.
  labels = tf.cast(labels, tf.int64)
  cross_entropy = tf.nn.sparse_softmax_cross_entropy_with_logits(
      logits, labels, name='cross_entropy_per_example')
  cross_entropy_mean = tf.reduce_mean(cross_entropy, name='cross_entropy')
  tf.add_to_collection('losses', cross_entropy_mean * (1.0 - FLAGS.lambda_regr))



def loss_regr (regressions, rois):
  """Add L2Loss to all the trainable variables.
  Add summary for for "Loss" and "Loss/avg".
  Args:
    regressions:  2D Tensor of type tf.int32, [batch_size, 4]
    rois:         2D Tensor of type tf.int32, [batch_size, 4]
  Returns:
    Loss tensor of type float.
  """
  assert regressions.get_shape()[0] == FLAGS.batch_size
  assert regressions.get_shape()[1] == 4

  # Calculate the total regression loss
  rois = tf.to_float(rois)
  regression_loss = tf.reduce_sum(L1_smooth(regressions - rois),
      reduction_indices=[1], name='regression_loss_per_example')
  regression_loss_mean = tf.reduce_mean(regression_loss, name='regr_loss')
  tf.add_to_collection('losses', regression_loss_mean * FLAGS.lambda_regr)



def _add_loss_summaries(total_loss):
  """Add summaries for losses in CIFAR-10 model.

  Generates moving average for all losses and associated summaries for
  visualizing the performance of the network.

  Args:
    total_loss: Total loss from loss().
  Returns:
    loss_averages_op: op for generating moving averages of losses.
  """
  # Compute the moving average of all individual losses and the total loss.
  loss_averages = tf.train.ExponentialMovingAverage(0.9, name='avg')
  losses = tf.get_collection('losses')
  loss_averages_op = loss_averages.apply(losses + [total_loss])

  # Attach a scalar summary to all individual losses and the total loss; do the
  # same for the averaged version of the losses.
  for l in losses + [total_loss]:
    # Name each loss as '(raw)' and name the moving average version of the loss
    # as the original loss name.
    tf.scalar_summary(l.op.name +' (raw)', l)
    tf.scalar_summary(l.op.name, loss_averages.average(l))

  return loss_averages_op


def train(total_loss, global_step):
  """Train CIFAR-10 model.

  Create an optimizer and apply to all trainable variables. Add moving
  average for all trainable variables.

  Args:
    total_loss: Total loss from loss().
    global_step: Integer Variable counting the number of training steps
      processed.
  Returns:
    train_op: op for training.
  """
  # Variables that affect learning rate.
  num_batches_per_epoch = NUM_EXAMPLES_PER_EPOCH_FOR_TRAIN / FLAGS.batch_size
  decay_steps = int(num_batches_per_epoch * FLAGS.NUM_EPOCHS_PER_DECAY)

  # Decay the learning rate exponentially based on the number of steps.
  lr = tf.train.exponential_decay(FLAGS.INITIAL_LEARNING_RATE,
                                  global_step,
                                  decay_steps,
                                  FLAGS.LEARNING_RATE_DECAY_FACTOR,
                                  staircase=True)
  tf.scalar_summary('learning_rate', lr)

  # Generate moving averages of all losses and associated summaries.
  loss_averages_op = _add_loss_summaries(total_loss)

  # Compute gradients.
  with tf.control_dependencies([loss_averages_op]):
    opt = tf.train.GradientDescentOptimizer(lr)
    grads = opt.compute_gradients(total_loss)

  # Apply gradients.
  apply_gradient_op = opt.apply_gradients(grads, global_step=global_step)

  # Add histograms for trainable variables.
  for var in tf.trainable_variables():
    tf.histogram_summary(var.op.name, var)

  # Add histograms for gradients.
  for grad, var in grads:
    if grad:
      tf.histogram_summary(var.op.name + '/gradients', grad)

  # Track the moving averages of all trainable variables.
  ema = tf.train.ExponentialMovingAverage(FLAGS.MOVING_AVERAGE_DECAY, global_step)
  variables_averages_op = ema.apply(tf.trainable_variables())

  with tf.control_dependencies([apply_gradient_op]): #, variables_averages_op]):
    train_op = tf.no_op(name='train')

  return train_op
