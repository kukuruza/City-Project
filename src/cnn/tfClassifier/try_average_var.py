import tensorflow as tf

with tf.Graph().as_default() as graph:
  #with tf.variable_scope('myscope') as scope:
  var = tf.get_variable(name='myvar', shape=[1],
                         initializer=tf.constant_initializer(0.0))

  variable_averages = tf.train.ExponentialMovingAverage(0.9, 0)
  variables_averages_op = variable_averages.apply(tf.trainable_variables())

  init_op = tf.initialize_all_variables()


  with tf.Session() as sess:
    #sess.run([init_op])

    #saver = tf.train.Saver(tf.all_variables())
    #saver.save(sess, '/tmp/test_checkpoint/model.ckpt', global_step=0)


    variable_averages = tf.train.ExponentialMovingAverage(0.9)
    variables_to_restore = variable_averages.variables_to_restore()
    saver = tf.train.Saver(variables_to_restore)
    ckpt = tf.train.get_checkpoint_state('/tmp/test_checkpoint')
    saver.restore(sess, ckpt.model_checkpoint_path)

