import logging
import argparse
import numpy as np
import cv2

def _div0( a, b ):
  ''' Ignore / 0, div0( [-1, 0, 1], 0 ) -> [0, 0, 0] '''
  with np.errstate(divide='ignore', invalid='ignore'):
    c = np.true_divide( a, b )
    c[ ~ np.isfinite( c )] = 0  # -inf inf NaN
  return c


def maskedDilation(img, kernel):
  ''' Zero neighbours of a pixel do not count in the result for that pixel. '''

  # Remember the type for output.
  dtype = img.dtype
  
  mask = (img > 0).astype(float)
  img = img.astype(float)

  assert len(kernel.shape) == 2, kernel.shape
  img = cv2.filter2D(img, -1, kernel)
  mask = cv2.filter2D(mask, -1, kernel)

  return _div0(img, mask).astype(dtype)


if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('--in_image_path', required=True)
  parser.add_argument('--out_image_path')
  parser.add_argument('--kernel_size', type=int, default=3)
  parser.add_argument('--logging', type=int, default=20, choices=[10,20,30,40])
  args = parser.parse_args()
  
  logging.basicConfig(level=args.logging, format='%(levelname)s: %(message)s')

  img = cv2.imread(args.in_image_path, -1)
  assert img is not None, args.in_image_path

  kernel = np.ones((args.kernel_size, args.kernel_size), dtype=float)
  out_img = maskedDilation(img, kernel)
  assert img.shape == out_img.shape, (img.shape, out_image.shape)

  if args.out_image_path:
    cv2.imwrite(args.out_image_path, out_img)

