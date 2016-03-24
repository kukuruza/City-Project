import os, os.path as op
import tensorflow as tf

import citycam

FLAGS = tf.app.flags.FLAGS

def atcity(x):
  return op.join(os.getenv('CITY_DATA_PATH'), x)

tf.app.flags.DEFINE_string('train_dir', '/tmp/try_bbox_and_mask', '')
tf.app.flags.DEFINE_string('data_dir',  atcity('augmentation/patches-Mar23'), '')
tf.app.flags.DEFINE_string('list_name', 'eval_list-vis60.txt', '')

tf.app.flags.DEFINE_integer('num_preprocess_threads', 1, '')



with tf.Graph().as_default() as graph:

  images, labels, rois, masks = citycam.distorted_inputs(FLAGS.list_name)

  with tf.Session() as sess:

    summary_op = tf.merge_all_summaries()
    summary_writer = tf.train.SummaryWriter(FLAGS.train_dir)

    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(sess=sess, coord=coord)

    with coord.stop_on_exception():
      for step in xrange(10):
        if coord.should_stop(): 
          break

        sess.run(images)

        summary_str = sess.run(summary_op)
        summary_writer.add_summary(summary_str, step)

    coord.request_stop()
    coord.join(threads, stop_grace_period_secs=10)
