import tensorflow as tf



def inference (x):
  W = tf.Variable(tf.zeros([784, 10]), name='W')
  b = tf.Variable(tf.zeros([10]), name='b')
  return tf.nn.softmax(tf.matmul(x, W) + b)



with tf.Graph().as_default() as graph:

  x_train = tf.placeholder(tf.float32, [None, 784], name='x_train')
  x_eval  = tf.placeholder(tf.float32, [None, 784], name='x_eval')

  with tf.variable_scope("model") as scope:
    y_train = inference(x_train)
    scope.reuse_variables()
    y_eval  = inference(x_eval)

  summary_writer = tf.train.SummaryWriter('/tmp/try_shared_train',
                                        graph_def=graph.as_graph_def())

