import numpy as np
import tensorflow as tf


def shared_op (x):

  a = tf.get_variable (name='a', shape=[1], initializer=tf.constant_initializer(1.0))
  return tf.maximum (x, a, name='my_maximum')


with tf.Graph().as_default() as graph:

  input1 = tf.placeholder(tf.float32, shape=[1], name='input1')
  input2 = tf.placeholder(tf.float32, shape=[1], name='input2')

  with tf.variable_scope("myscope") as scope:
    output1 = shared_op(input1)
    scope.reuse_variables()
    output2 = shared_op(input2)

  result1 = tf.add(output1, 1, name='add1')
  result2 = tf.add(output2, 2, name='add2')

  summary_writer = tf.train.SummaryWriter('/tmp/try_share_inference',
                                          graph_def=graph.as_graph_def())

