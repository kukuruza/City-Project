import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
from glob import glob
from time import sleep, time
import json
import logging
import numpy as np
import cv2
import argparse
from skimage import color
from learning.helperSetup import setParamUnlessThere



def unsharp_mask (img, params={}):

  setParamUnlessThere (params, 'radius', 4.7)
  setParamUnlessThere (params, 'threshold', 23)
  setParamUnlessThere (params, 'amount', 5)
  radius    = params['radius']
  threshold = params['threshold']
  amount    = params['amount']

  with_alpha = False
  if img.shape[2] == 4:
    alpha = img[:,:,3]
    img = img[:,:,0:3]
    with_alpha = True

  blur_rad = int(radius) * 2 + 1
  blurred = cv2.GaussianBlur (img, (blur_rad, blur_rad), radius)
  lowContrastMask = np.abs(img - blurred) < threshold;
  sharpened = img.astype(float) * (1+amount) + blurred.astype(float) * (-amount);
  sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
  sharpened[lowContrastMask] = img[lowContrastMask]

  if with_alpha:
    sharpened = np.dstack((sharpened, alpha))

  return sharpened



def color_correction (img_ref, img_target):
    if img_ref is None or img_target is None:
        logging.error ('''color_correction: img_ref or img_target is None. 
                          Colors will not be corrected''')
        return {'dh': 0, 'ds': 0, 'dv': 0}

    hsv_ref = color.rgb2hsv(color.gray2rgb(img_ref))
    hsv_tgt = color.rgb2hsv(color.gray2rgb(img_target))

    h_ref = np.mean(hsv_ref[:,:,0])
    s_ref = np.mean(hsv_ref[:,:,1])
    v_ref = np.mean(hsv_ref[:,:,2])
    h_tgt = np.mean(hsv_tgt[:,:,0])
    s_tgt = np.mean(hsv_tgt[:,:,1])
    v_tgt = np.mean(hsv_tgt[:,:,2])

    logging.info ('color_correction: mean ref hsv: %.2f,%.2f,%.2f' % (h_ref, s_ref, v_ref))
    logging.info ('color_correction: mean tgt hsv: %.2f,%.2f,%.2f' % (h_tgt, s_tgt, v_tgt))

    # img_corr = img_target.copy()
    # img_corr[:,:,0] = h_ref
    # img_corr[:,:,1] = s_ref
    # img_corr = np.multiply (color.hsv2rgb(hsv_target), 255).astype(np.uint8)
    # stacked = np.vstack((img_ref, img_target, img_corr))
    # cv2.imshow('test', stacked)
    # cv2.waitKey(-1)

    return {'dh': (h_ref - h_tgt) * 0.5, 
            'ds': (s_ref - s_tgt) * 2, 
            'dv': (v_ref - v_tgt) * 2}


