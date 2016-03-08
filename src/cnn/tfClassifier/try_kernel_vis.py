import cv2
import numpy as np
import tensorflow as tf

icons = cv2.imread('/Users/evg/Desktop/icons.jpg')

Y = icons.shape[0] / 2
X = icons.shape[1] / 3
icon1 = np.expand_dims(icons[0:Y,   0:X, :], 3)
icon2 = np.expand_dims(icons[Y:Y*2, 0:X, :], 3)
icon3 = np.expand_dims(icons[0:Y,   X:X*2,:], 3)
icon4 = np.expand_dims(icons[Y:Y*2, X:X*2,:], 3)
icon5 = np.expand_dims(icons[0:Y,   X*2:X*3,:], 3)
icon6 = np.expand_dims(icons[Y:Y*2, X*2:X*3,:], 3)
icons = np.concatenate((icon1,icon2,icon3,icon4,icon5,icon6), axis=3)
print icons.shape



def put_kernels_on_grid (kernel, (grid_Y, grid_X), pad=1):
    '''Visualize conv. features as an image (mostly for the 1st layer).
    Place kernel into a grid, with some paddings between adjacent filters.

    Args:
      kernel:            tensor of shape [Y, X, NumChannels, NumKernels]
      (grid_Y, grid_X):  shape of the grid. Require: NumKernels == grid_Y * grid_X
                           User is responsible of how to break into two multiples.
      pad:               number of black pixels around each filter (between them)
    
    Return:
      Tensor of shape [(Y+2*pad)*grid_Y, (X+2*pad)*grid_X, NumChannels, 1].
    '''
    # pad X and Y
    x1 = tf.pad(kernel, tf.constant( [[pad,pad],[pad, pad],[0,0],[0,0]] ))

    # X and Y dimensions, w.r.t. padding
    Y = kernel.get_shape()[0] + 2 * pad
    X = kernel.get_shape()[1] + 2 * pad

    # put NumKernels to the 1st dimension
    x2 = tf.transpose(x1, (3, 0, 1, 2))
    # organize grid on Y axis
    x3 = tf.reshape(x2, tf.pack([grid_X, Y * grid_Y, X, 3]))
    
    # switch X and Y axes
    x4 = tf.transpose(x3, (0, 2, 1, 3))
    # organize grid on X axis
    x5 = tf.reshape(x4, tf.pack([1, X * grid_X, Y * grid_Y, 3]))
    
    # back to normal order (not combining with the next step for clarity)
    x6 = tf.transpose(x5, (2, 1, 3, 0))

    # to tf.image_summary order [batch_size, height, width, channels],
    #   where in this case batch_size == 1
    x7 = tf.transpose(x6, (3, 0, 1, 2))

    # scale to [0, 1]
    x_min = tf.reduce_min(x7)
    x_max = tf.reduce_max(x7)
    x8 = (x7 - x_min) / (x_max - x_min)

    # scale to [0, 255] and convert to uint8
    return tf.image.convert_image_dtype(x8, dtype=tf.uint8)


x = tf.placeholder(tf.uint8, shape=(Y, X, 3, 6))

grid_X = 2
grid_Y = 3
y = tf.to_float(x) / 255 * 0.5 - 0.4
reshaped = put_kernels_on_grid (y, (grid_Y, grid_X))

with tf.Session() as sess:
    
    icons = sess.run([reshaped], feed_dict={x: np.array(icons, dtype=np.uint8)})[0]
    icons = np.transpose(icons, [1,2,3,0])

    print icons.shape
    print icons.dtype
    cv2.imshow('test', icons[:,:,:,0])
    cv2.waitKey(-1)
