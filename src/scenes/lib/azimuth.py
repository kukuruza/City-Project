import os.path as op
import numpy as np
import cv2


def read_azimuth_image(azimuth_path):
  ''' Take care of reading the image and respect the conventions. '''

  assert op.exists(azimuth_path), azimuth_path
  azimuth = cv2.imread(azimuth_path, -1)
  assert azimuth is not None
  # Mask is in the alpha channel, the other 3 channels are the same value.
  mask = azimuth[:,:,3] > 0
  azimuth = azimuth[:,:,0].astype(float)
  # By convention, azimuth angles are divided by 2 before written to image.
  azimuth *= 2
  return azimuth, mask


def write_azimuth_image(azimuth_path, azimuth, mask=None):
  ''' Take care of wrting the image and respect the conventions. '''

  # By convention, azimuth angles are divided by 2 before written to image.
  azimuth = azimuth.copy() / 2.

  # By convention to be human-friendly, write as 8bit.
  azimuth = azimuth.astype(np.uint8)

  assert len(azimuth.shape) == 2, 'Need grayscale azimuth.'
  if mask is None:
    mask = np.ones(azimuth.shape, dtype=np.uint8) * 255
  else:
    assert mask.shape == azimuth.shape
    mask = mask.astype(np.uint8)
    mask[mask > 0] = 255

  # Mask is in the alpha channel, the other 3 channels are the same value.
  azimuth = np.stack((azimuth, azimuth, azimuth, mask), axis=-1)
  cv2.imwrite(azimuth_path, azimuth)
