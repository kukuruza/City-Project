from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os, os.path as op
import re
import sys
import tarfile

import tensorflow as tf

import citycam_input


FLAGS = tf.app.flags.FLAGS

# Basic model parameters. UPDATE: set in main()
tf.app.flags.DEFINE_integer('batch_size', 128,
                            """Number of images to process in a batch.""")
# tf.app.flags.DEFINE_string('data_dir', 
#               op.join(os.getenv('CITY_DATA_PATH'), 'augmentation/patches'),
#                            """Path to the citycam data directory.""")


# Global constants describing the citycam data set.
IMAGE_WIDTH  = citycam_input.IMAGE_WIDTH
IMAGE_HEIGHT = citycam_input.IMAGE_HEIGHT
NUM_CHANNELS = citycam_input.NUM_CHANNELS
NUM_CLASSES  = citycam_input.NUM_CLASSES
NUM_EXAMPLES_PER_EPOCH_FOR_TRAIN = citycam_input.NUM_EXAMPLES_PER_EPOCH_FOR_TRAIN
NUM_EXAMPLES_PER_EPOCH_FOR_EVAL  = citycam_input.NUM_EXAMPLES_PER_EPOCH_FOR_EVAL


# Constants describing the training process.
MOVING_AVERAGE_DECAY = 0.9999     # The decay to use for the moving average.
# NUM_EPOCHS_PER_DECAY = 350.0      # Epochs after which learning rate decays.
# LEARNING_RATE_DECAY_FACTOR = 0.1  # Learning rate decay factor.
# INITIAL_LEARNING_RATE = 0.1       # Initial learning rate.

# If a model is trained with multiple GPU's prefix all Op names with tower_name
# to differentiate the operations. Note that this prefix is removed from the
# names of the summaries when visualizing a model.
TOWER_NAME = 'tower'

tf.app.flags.DEFINE_float('MOVING_AVERAGE_DECAY', MOVING_AVERAGE_DECAY, '')



# def setupLogging (filename, level=logging.INFO, filemode='w'):
#     log = logging.getLogger('')
#     formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s: \t%(message)s')
#     log.setLevel(level)

#     log_path = os.path.join (os.getenv('CITY_PATH'), filename)
#     if not op.exists (op.dirname(log_path)):
#         os.makedirs (op.dirname(log_path))
#     fh = logging.handlers.RotatingFileHandler(log_path, mode=filemode)
#     fh.setFormatter(formatter)
#     log.addHandler(fh)

#     sh = logging.StreamHandler(sys.stdout)
#     sh.setFormatter(formatter)
#     log.addHandler(sh)



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


def _variable_on_cpu(name, shape, initializer):
  """Helper to create a Variable stored on CPU memory.

  Args:
    name: name of the variable
    shape: list of ints
    initializer: initializer for Variable

  Returns:
    Variable Tensor
  """
  with tf.device('/cpu:0'):
    var = tf.get_variable(name, shape, initializer=initializer)
  return var


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
  var = _variable_on_cpu(name, shape,
                         tf.truncated_normal_initializer(stddev=stddev))
  if wd:
    weight_decay = tf.mul(tf.nn.l2_loss(var), wd, name='weight_loss')
    tf.add_to_collection('losses', weight_decay)
  return var


def distorted_inputs (data_list_name, dataset_tag=''):
  """Construct distorted input for CIFAR training using the Reader ops.

  Returns:
    images: Images. 4D tensor of 
               [batch_size, IMAGE_HEIGHT, IMAGE_WIDTH, NUM_CHANNELS] size.
    labels: Labels. 1D tensor of [batch_size] size.

  Raises:
    ValueError: If no data_dir
  """
  if not FLAGS.data_dir:
    raise ValueError('Please supply a data_dir')
  train_list_path = os.path.join(FLAGS.data_dir, data_list_name)
  return citycam_input.distorted_inputs(train_list_path, FLAGS.batch_size, 
                                        '/'+op.splitext(data_list_name)[0])


def inputs (data_list_name, dataset_tag=''):
  """Construct input for CIFAR evaluation using the Reader ops.

  Returns:
    images: Images. 4D tensor of 
               [batch_size, IMAGE_HEIGHT, IMAGE_WIDTH, NUM_CHANNELS] size.
    labels: Labels. 1D tensor of [batch_size] size.

  Raises:
    ValueError: If no data_dir
  """
  if not FLAGS.data_dir:
    raise ValueError('Please supply a data_dir')
  data_list_path = os.path.join(FLAGS.data_dir, data_list_name)
  return citycam_input.inputs(data_list_path, FLAGS.batch_size,
                              '/'+op.splitext(data_list_name)[0])




def put_kernels_on_grid (kernel, (grid_Y, grid_X), pad=1):
  '''Visualize conv. features as an image (mostly for the 1st layer).
  Place kernel into a grid, with some paddings between adjacent filters.

  Args:
    kernel:            tensor of shape [Y, X, NumChannels, NumKernels]
    (grid_Y, grid_X):  shape of the grid. Require: NumKernels == grid_Y * grid_X
                         User is responsible of how to break into two multiples.
    pad:               number of black pixels around each filter (between them)
  
  Return:
    Tensor of shape [(Y+pad)*grid_Y, (X+pad)*grid_X, NumChannels, 1].
  '''
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
  x3 = tf.reshape(x2, tf.pack([grid_X, Y * grid_Y, X, 3]))
  
  # switch X and Y axes
  x4 = tf.transpose(x3, (0, 2, 1, 3))
  # organize grid on X axis
  x5 = tf.reshape(x4, tf.pack([1, X * grid_X, Y * grid_Y, 3]))
  
  # back to normal order (not combining with the next step for clarity)
  x6 = tf.transpose(x5, (2, 1, 3, 0))

  # to tf.image_summary order [batch_size, height, width, channels],
  #   where in this case batch_size == 1
  return tf.transpose(x6, (3, 0, 1, 2))


def predict (logits_op, labels_op):
  correct_op = tf.nn.in_top_k (logits_op, labels_op, 1)
  predicted_op = tf.argmax(logits_op, 1)

  return correct_op, predicted_op, labels_op



def inference(images):
  """Build the CIFAR-10 model.

  Args:
    images: Images returned from distorted_inputs() or inputs().

  Returns:
    Logits.
  """
  # We instantiate all variables using tf.get_variable() instead of
  # tf.Variable() in order to share variables across multiple GPU training runs.
  # If we only ran this model on a single GPU, we could simplify this function
  # by replacing all instances of tf.get_variable() with tf.Variable().
  #
  # conv1
  with tf.variable_scope('conv1') as scope:
    kernel = _variable_with_weight_decay('weights', shape=[5, 5, 3, 64],
                                         stddev=1e-4, wd=0.0)
    conv = tf.nn.conv2d(images, kernel, [1, 1, 1, 1], padding='SAME')
    biases = _variable_on_cpu('biases', [64], tf.constant_initializer(0.0))
    bias = tf.nn.bias_add(conv, biases)
    conv1 = tf.nn.relu(bias, name=scope.name)
    _activation_summary(conv1)

  # pool1
  pool1 = tf.nn.max_pool(conv1, ksize=[1, 3, 3, 1], strides=[1, 2, 2, 1],
                         padding='SAME', name='pool1')
  # norm1
  norm1 = tf.nn.lrn(pool1, 4, bias=1.0, alpha=0.001 / 9.0, beta=0.75,
                    name='norm1')

  # conv2
  with tf.variable_scope('conv2') as scope:
    kernel = _variable_with_weight_decay('weights', shape=[5, 5, 64, 64],
                                         stddev=1e-4, wd=0.0)
    conv = tf.nn.conv2d(norm1, kernel, [1, 1, 1, 1], padding='SAME')
    biases = _variable_on_cpu('biases', [64], tf.constant_initializer(0.1))
    bias = tf.nn.bias_add(conv, biases)
    conv2 = tf.nn.relu(bias, name=scope.name)
    _activation_summary(conv2)

  # norm2
  norm2 = tf.nn.lrn(conv2, 4, bias=1.0, alpha=0.001 / 9.0, beta=0.75,
                    name='norm2')
  # pool2
  pool2 = tf.nn.max_pool(norm2, ksize=[1, 3, 3, 1],
                         strides=[1, 2, 2, 1], padding='SAME', name='pool2')

  # local3
  with tf.variable_scope('local3') as scope:
    # Move everything into depth so we can perform a single matrix multiply.
    dim = 1
    for d in pool2.get_shape()[1:].as_list():
      dim *= d
    reshape = tf.reshape(pool2, [FLAGS.batch_size, dim])

    weights = _variable_with_weight_decay('weights', shape=[dim, 384],
                                          stddev=0.04, wd=0.004)
    biases = _variable_on_cpu('biases', [384], tf.constant_initializer(0.1))
    local3 = tf.nn.relu(tf.matmul(reshape, weights) + biases, name=scope.name)
    #_activation_summary(local3)

  # local4
  with tf.variable_scope('local4') as scope:
    weights = _variable_with_weight_decay('weights', shape=[384, 192],
                                          stddev=0.04, wd=0.004)
    biases = _variable_on_cpu('biases', [192], tf.constant_initializer(0.1))
    local4 = tf.nn.relu(tf.matmul(local3, weights) + biases, name=scope.name)
    #_activation_summary(local4)

  # softmax, i.e. softmax(WX + b)
  with tf.variable_scope('softmax_linear') as scope:
    weights = _variable_with_weight_decay('weights', [192, NUM_CLASSES],
                                          stddev=1/192.0, wd=0.0)
    biases = _variable_on_cpu('biases', [NUM_CLASSES],
                              tf.constant_initializer(0.0))
    softmax_linear = tf.add(tf.matmul(local4, weights), biases, name=scope.name)
    #_activation_summary(softmax_linear)

  return softmax_linear



def loss(logits, labels):
  """Add L2Loss to all the trainable variables.

  Add summary for for "Loss" and "Loss/avg".
  Args:
    logits: Logits from inference().
    labels: Labels from distorted_inputs or inputs(). 1-D tensor
            of shape [batch_size]

  Returns:
    Loss tensor of type float.
  """
  # Calculate the average cross entropy loss across the batch.
  labels = tf.cast(labels, tf.int64)
  cross_entropy = tf.nn.sparse_softmax_cross_entropy_with_logits(
      logits, labels, name='cross_entropy_per_example')
  cross_entropy_mean = tf.reduce_mean(cross_entropy, name='cross_entropy')
  tf.add_to_collection('losses', cross_entropy_mean)

  # The total loss is defined as the cross entropy loss plus all of the weight
  # decay terms (L2 loss).
  return tf.add_n(tf.get_collection('losses'), name='total_loss')


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
  variable_averages = tf.train.ExponentialMovingAverage(
      FLAGS.MOVING_AVERAGE_DECAY, global_step)
  variables_averages_op = variable_averages.apply(tf.trainable_variables())

  with tf.control_dependencies([apply_gradient_op, variables_averages_op]):
    train_op = tf.no_op(name='train')

  return train_op