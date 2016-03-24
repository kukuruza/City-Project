import tensorflow as tf

def L1_smooth(x):
  return tf.select (tf.greater(x, 1.0), tf.abs(x)-0.5, 0.5*tf.square(x))

def loss_regr(y_, y);
  return tf.reduce_sum (L1_smooth(y - y_))


with tf.Graph().as_default() as graph:
  x = tf.placeholder(tf.float32, shape=[None])
  y = L1_smooth(x)

  with tf.Session() as sess:
    print y.eval(feed_dict={x: [-1, -0.5, 0, 0.25, 0.5, 1, 2]})
