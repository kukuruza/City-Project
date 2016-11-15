import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('HOME'), 'src/tensorflow-fcn'))
import tensorflow as tf
import argparse

import numpy as np
import skimage.io
import scipy as scp
import scipy.misc
import cv2

import fcn32_vgg
import utils

import configs



def deploy(img, init_npy_path, checkpoint_path, out_dir):
  '''
  Runs the whole batch, which has multiple copies of the same image :(
  Args:
    init_npy_path: used to workaround the fact that 
                   fcn32_vgg.FCN32VGG cannot be build without a dict
  '''
  # prepare the image
  img = img.astype(float)
  img = cv2.resize(img, configs.IMG_SIZE)
  img = (img - configs.COLOR_MEAN_BGR) / 255.0
  img_batch = np.repeat(img[np.newaxis,:], configs.BATCH_SIZE, axis=0)
  print 'img_batch shape', img_batch.shape, 'type', img_batch.dtype

  vgg_fcn = fcn32_vgg.FCN32VGG(init_npy_path)

  input_shape = [configs.BATCH_SIZE, configs.IMG_SIZE[1], configs.IMG_SIZE[0]]
  ph_x = tf.placeholder(tf.float32, input_shape + [3])
  with tf.name_scope("content_vgg"):
    vgg_fcn.build(ph_x, train=False, num_classes=2,
                  debug=True)
  
  print('Finished building Network.')

  saver = tf.train.Saver()

  with tf.Session() as sess:
    sess.run(tf.initialize_all_variables())
    saver.restore(sess, checkpoint_path)
    print('Running the Network')

    down, up = sess.run([vgg_fcn.pred, vgg_fcn.pred_up], feed_dict={ph_x: img_batch})

  down_color = utils.color_image(down[0])
  up_color = utils.color_image(up[0])

  if out_dir is not None:
    scp.misc.imsave(op.join(out_dir, 'fcn32_downsampled.png'), down_color)
    scp.misc.imsave(op.join(out_dir, 'fcn32_upsampled.png'), up_color)



if __name__ == '__main__':
  np.random.seed(2016)
  
  parser = argparse.ArgumentParser()
  parser.add_argument('--init_npy_path', required=True)
  parser.add_argument('--checkpoint_path', required=True)
  parser.add_argument('--image_path', required=True)
  parser.add_argument('--out_dir', help='directory for output')
  args = parser.parse_args()

  img = skimage.io.imread(args.image_path)

  deploy(img, args.init_npy_path, args.checkpoint_path, args.out_dir)

