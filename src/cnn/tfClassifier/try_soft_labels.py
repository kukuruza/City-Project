import numpy as np
import tensorflow as tf

def soften_labels (labels, kernel_val):
  L = labels.get_shape()[1].value

  # prepare the kernel
  kernel = tf.constant(kernel_val)
  kernel = tf.expand_dims(tf.expand_dims(tf.expand_dims(kernel,-1),-1),-1)

  # expand the same length on both sides
  labels = tf.pad(labels, paddings=[[0,0],[L,L]])

  # do conv2d for 4D tensor
  labels = tf.expand_dims(tf.expand_dims(labels,-1),-1)
  labels = tf.nn.conv2d (labels, filter=kernel, strides=[1,1,1,1], padding='SAME')
  labels = tf.squeeze(labels)

  # wrap the result around the sides
  labels_left   = tf.slice(labels, begin=[0,0],   size=[-1,L])
  labels_center = tf.slice(labels, begin=[0,L],   size=[-1,L])
  labels_right  = tf.slice(labels, begin=[0,L*2], size=[-1,L])
  labels = labels_left + labels_center + labels_right

  return labels



batch_size = 2
num_classes = 10
kernel_val = [0.0044, 0.0540, 0.2420, 0.3989, 0.2420, 0.0540, 0.0044]
print 'kernel shape: %d' % len(kernel_val)

dense_labels_in = tf.constant([[0,0,1,0,0,0,0,0,0,0],[1,0,0,0,0,0,0,0,0,0]], 
                              dtype=tf.float32)
print 'labels in shape: %s' % str(dense_labels_in.get_shape())


soft_labels_out = soften_labels(dense_labels_in, kernel_val)

with tf.Session() as sess:
  labels_val = sess.run(soft_labels_out)

np.set_printoptions(precision=3)
print labels_val

