import numpy as np
import os
import numpy as np
import tensorflow as tf
import cv2
import configs
import sys, os, os.path as op
sys.path.insert(0, '/Users/evg/src/tensorflow-fcn/vgg16.npy')


def model(x):
    # make inputs
    # input_shape: [clip_length, height, width, channels]
    input_shape = x.get_shape().as_list()[1:]
    assert len(input_shape) == 4
    # create network
    preds = []
    with tf.variable_scope(
            'conv_lstm', initializer=tf.random_uniform_initializer(-.01, 0.1)):
        cell = BasicConvLSTMCell(input_shape[1 : 3], [3, 3], 64)
        new_state = cell.zero_state(configs.BATCH_SIZE, tf.float32) 
        print 'hidden state:', new_state.get_shape().as_list()

    # conv network
    for i in range(input_shape[0]):
        conv1 = ld.conv_layer(x[:, i, :, :, :], 3, 1, 64, "conv_1")
        conv2 = ld.conv_layer(conv1, 3, 1, 32, "conv_2")
        conv3 = ld.conv_layer(conv2, 3, 1, 32, "conv_3")
        conv_lstm1, new_state = cell(conv3, new_state)
        # conv4 = ld.conv_layer(conv_lstm1, 1, 1, 2, "conv_4")
        conv5 = ld.transpose_conv_layer(conv_lstm1, 3, 1, 32, "deconv_5")
        conv6 = ld.transpose_conv_layer(conv_lstm1, 3, 1, 8, "deconv_6")
        conv7 = ld.transpose_conv_layer(conv_lstm1, 3, 1, 2, "deconv_7", True)
        preds.append(tf.expand_dims(conv7, 1))
        if i == 0:
            tf.get_variable_scope().reuse_variables()

    return tf.concat(1, preds)


def compute_loss(gt, preds, pos_weight):
    preds = tf.nn.softmax(preds)
    loss  = tf.nn.weighted_cross_entropy_with_logits(preds, gt, tf.constant([1-pos_weight, pos_weight]))
    return tf.reduce_mean(loss)


if __name__ == '__main__':
    input_shape = [10, 320, 320, 3]
    x = tf.placeholder(tf.float32, [None] + input_shape)
    preds = build_model(x)
