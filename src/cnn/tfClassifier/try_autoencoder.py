import os, os.path as op
import tensorflow as tf

import citycam

FLAGS = tf.app.flags.FLAGS

def atcity(x):
  return op.join(os.getenv('CITY_DATA_PATH'), x)

tf.app.flags.DEFINE_string('train_dir', '/tmp/try_autoencoder-2', '')
tf.app.flags.DEFINE_string('data_dir',  atcity('augmentation/patches-Mar23'), '')
tf.app.flags.DEFINE_string('list_name', 'train_list-vis60.txt', '')

tf.app.flags.DEFINE_integer('batch_size', 8, '')
tf.app.flags.DEFINE_integer('num_preprocess_threads', 1, '')




def l1_loss(x):
  return tf.reduce_mean(tf.abs(x))


def l2_loss(x):
  return tf.reduce_mean(tf.square(x))  


def make_conv(input_, kernel, name, padding):
  with tf.variable_scope(name) as scope:
    conv = tf.nn.conv2d(input_, kernel, [1, 1, 1, 1], padding=padding)
    biases = tf.get_variable('biases', [kernel.get_shape()[3]], 
                             initializer=tf.constant_initializer(0.0))
    bias = tf.nn.bias_add(conv, biases)
    conv_layer = tf.nn.relu(bias, name=scope.name)
  return conv_layer


def make_unpooling (conv, pool):
  h = conv.get_shape()[1]
  w = conv.get_shape()[2]
  resized = tf.image.resize_images (pool, h, w, method=1)
  zeros   = tf.zeros (resized.get_shape())
  return tf.select (tf.greater(resized, conv), zeros, conv)


def make_norm(input_, name):
  return tf.nn.lrn(input_, 4, bias=1.0, alpha=0.001 / 9.0, beta=0.75, name=name)


def inference(images):
  shape = [5, 5, 3, 32]
  wd = 0.1

  im_height = im_width = 61

  assert images.get_shape()[1] == im_height and \
         images.get_shape()[2] == im_width, \
         'images shape: %s' % str(images.get_shape())

  # kernel1
  kernel_forw = tf.get_variable('weights', shape,
                 initializer=tf.contrib.layers.xavier_initializer_conv2d())
  kernel_back = tf.transpose(kernel_forw, [0,1,3,2])
  tf.image_summary('kernel', citycam.put_kernels_on_grid(kernel_forw), max_images=1)

  # conv1 + pool1
  conv1 = make_conv(images, kernel_forw, 'conv1', padding='SAME')
  pool1 = tf.nn.max_pool(conv1, padding='SAME', ksize=[1,2,2,1], strides=[1,2,2,1])

  tf.add_to_collection('losses', l1_loss(pool1))

  # unpool1 + deconv1
  unpool1 = make_unpooling (conv1, pool1)
  deco1 = make_conv(unpool1, kernel_back, 'deco1', padding='SAME')

  assert images.get_shape() == deco1.get_shape()

  grid = tf.concat(1, [tf.concat(2, [images, deco1]),
                       tf.concat(2, [tf.slice(unpool1, [0,0,0,0], [-1,-1,-1,3]), 
                                     tf.slice(unpool1, [0,0,0,3], [-1,-1,-1,3])
                                    ])])
  tf.image_summary('images', grid, max_images=5)

  return deco1



with tf.Graph().as_default() as graph:
  global_step = tf.Variable(0, trainable=False, name='global_step')

  images, _, _, _ = citycam.distorted_inputs(FLAGS.list_name)

  deco1 = inference(images)
  tf.add_to_collection('losses', l2_loss(images - deco1))
  total_loss = tf.add_n(tf.get_collection('losses'))

  train_op = tf.train.GradientDescentOptimizer(0.01).minimize(total_loss)

  summary_op = tf.merge_all_summaries()
  summary_writer = tf.train.SummaryWriter(FLAGS.train_dir)

  with tf.Session() as sess:

    init = tf.initialize_all_variables()
    sess.run(init)

    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(sess=sess, coord=coord)

    with coord.stop_on_exception():
      for step in xrange(2000):
        if coord.should_stop(): 
          break

        _, loss_val = sess.run([train_op, total_loss])
        print ('step %d, loss = %.6f' % (step, loss_val))

        if step % 100 == 0:
          summary_str = sess.run(summary_op)
          summary_writer.add_summary(summary_str, step)

    coord.request_stop()
    coord.join(threads, stop_grace_period_secs=10)
