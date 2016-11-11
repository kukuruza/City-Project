import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('HOME'), 'src/tensorflow-fcn'))
import tensorflow as tf
import argparse

import numpy as np
import skimage.io
import scipy as scp
import scipy.misc

import fcn32_vgg
import utils

import configs



def deploy(img, model_path, out_dir):

  vgg_fcn = fcn32_vgg.FCN32VGG(model_path)

  images = tf.placeholder("float")
  batch_images = tf.expand_dims(images, 0)
  with tf.name_scope("content_vgg"):
    vgg_fcn.build(batch_images, debug=True)
  print('Finished building Network.')

  with tf.Session() as sess:
    sess.run(tf.initialize_all_variables())

    print('Running the Network')
    down, up = sess.run([vgg_fcn.pred, vgg_fcn.pred_up], feed_dict={images: img})

  down_color = utils.color_image(down[0])
  up_color = utils.color_image(up[0])

  if out_dir is not None:
    scp.misc.imsave(op.join(out_dir, 'fcn32_downsampled.png'), down_color)
    scp.misc.imsave(op.join(out_dir, 'fcn32_upsampled.png'), up_color)



if __name__ == '__main__':
  np.random.seed(2016)
  
  parser = argparse.ArgumentParser()
  parser.add_argument('--model_path', required=True)
  parser.add_argument('--image_path', required=True)
  parser.add_argument('--out_dir', help='directory for output')
  args = parser.parse_args()

  img = skimage.io.imread(args.image_path)

  deploy(img, args.model_path, args.out_dir)

