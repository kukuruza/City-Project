import os, os.path as op
import tensorflow as tf

import citycam

FLAGS = tf.app.flags.FLAGS

def atcity(x):
  return op.join(os.getenv('CITY_DATA_PATH'), x)

tf.app.flags.DEFINE_string('train_dir', '/tmp/try_autoencoder', '')
tf.app.flags.DEFINE_string('data_dir',  atcity('augmentation/patches-Mar23'), '')
tf.app.flags.DEFINE_string('list_name', 'train_list-vis60.txt', '')

tf.app.flags.DEFINE_integer('batch_size', 128, '')
tf.app.flags.DEFINE_integer('num_preprocess_threads', 1, '')



def inference(images):
  assert images.get_shape()[1] == 61 and images.get_shape()[2] == 61, \
         'images shape: %s' % str(images.get_shape())

  shape = [7, 7, 3, 32]
  stddev = 0.05
  print ('initialize conv layer %s with xavier uniform with scale %f' % ('1', stddev))
  kernel_forw = tf.get_variable('weights', shape,
                 initializer=tf.random_uniform_initializer(minval=-stddev, maxval=stddev))
  kernel_back = tf.transpose(kernel_forw, [0,1,3,2])

  conv_f = tf.nn.conv2d(images, kernel_forw, [1, 1, 1, 1], padding='SAME')
  biases_f = tf.get_variable('biases_f', [shape[3]], initializer=tf.constant_initializer(0.0))
  bias_f = tf.nn.bias_add(conv_f, biases_f)
  conv1 = tf.nn.relu(bias_f, 'conv1')

  # norm1 = make_norm     (conv1,  name='norm1') 

  conv_b = tf.nn.conv2d(conv1, kernel_back, [1, 1, 1, 1], padding='SAME')
  biases_b = tf.get_variable('biases_b', [shape[2]], initializer=tf.constant_initializer(0.0))
  bias_b = tf.nn.bias_add(conv_b, biases_b)
  deco1 = tf.nn.relu(bias_b, 'deco1')
  
  assert images.get_shape() == deco1.get_shape()

  return deco1, (conv1, deco1)



with tf.Graph().as_default() as graph:
  global_step = tf.Variable(0, trainable=False, name='global_step')

  images, _, _, _ = citycam.distorted_inputs(FLAGS.list_name)

  with tf.variable_scope("inference") as scope:
    reconstructed, _ = inference(images)
    scope.reuse_variables()
    kernel = citycam.put_kernels_on_grid(tf.get_variable('weights'))
    tf.image_summary('weights', kernel, max_images=1)

  loss = tf.reduce_mean(tf.square(reconstructed - images))

  opt = tf.train.GradientDescentOptimizer(0.1)
  grads = opt.compute_gradients(loss)
  apply_gradient_op = opt.apply_gradients(grads, global_step=global_step)
  with tf.control_dependencies([apply_gradient_op]):
    train_op = tf.no_op(name='train')


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

        _, loss_val = sess.run([train_op, loss])
        print ('step %d, loss = %.2f' % (step, loss_val))

        if step % 100 == 0:
          summary_str = sess.run(summary_op)
          summary_writer.add_summary(summary_str, step)

    coord.request_stop()
    coord.join(threads, stop_grace_period_secs=10)
