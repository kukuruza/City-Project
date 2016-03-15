import os, sys, os.path as op
import logging
import shutil
import cv2


def _atcity(x):
  return op.join(os.getenv('CITY_DATA_PATH'), x)


def _open_video_capture (in_video_file):
  ''' Open video and set up bookkeeping '''
  logging.info ('opening video: %s' % in_video_file)
  videopath = _atcity(in_video_file)
  if not op.exists (videopath):
    raise Exception('videopath does not exist: %s' % videopath)
  handle = cv2.VideoCapture(videopath)  # open video
  if not handle.isOpened():
    raise Exception('video failed to open: %s' % videopath)
  return handle


def video2images (in_video_file, out_images_dir, ext='jpg'):
  '''
  Args:
    video_file:      path relative to $CITY_DATA_PATH
    out_images_dir:  path relative to $CITY_DATA_PATH
  '''
  # if a path is relative to CITY_DATA_PATH
  if out_images_dir[0] != '/':
    out_images_dir = _atcity(out_images_dir)
    logging.info ('consider the output path relative to CITY_DATA_PATH path')

  # delete if exists and recreate out dir
  if op.exists(out_images_dir):
    shutil.rmtree(out_images_dir)
  os.makedirs(out_images_dir)

  video = _open_video_capture (in_video_file)

  i = 0
  while video.isOpened():
    ret, frame = video.read()
    if not ret: break

    path = _atcity(op.join(out_images_dir, '%06d.%s' % (i, ext)))
    cv2.imwrite(path, frame)

    i += 1

  logging.info ('successfully wrote %d images to %s' % (i, out_images_dir))
  video.release()