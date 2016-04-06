import os, sys, os.path as op
import numpy as np
import cv2
import logging
import argparse
import time


def _openVideoCapture_ (videopath, relpath):
  ''' Open video and set up bookkeeping '''
  logging.info ('opening video: %s' % videopath)
  videopath = op.join (relpath, videopath)
  if not op.exists (videopath):
    raise Exception('videopath does not exist: %s' % videopath)
  handle = cv2.VideoCapture(videopath)  # open video
  if not handle.isOpened():
    raise Exception('video failed to open: %s' % videopath)
  return handle


def _openVideoWriter_ (videopath, ref_video, (width, height), relpath):
  ''' opens a video for writing with 2x by 2x frame size '''
  #width  = int(ref_video.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH))
  #height = int(ref_video.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
  fourcc = int(ref_video.get(cv2.cv.CV_CAP_PROP_FOURCC))
  fps    =     ref_video.get(cv2.cv.CV_CAP_PROP_FPS)
  #frame_size = (int(width * multx), int(height * multy))

  print ('opening video: %s' % videopath)
  print ('frame size: %dx%d, framerate %f' % (width, height, fps))
  videopath = op.join (relpath, videopath)
  handle = cv2.VideoWriter (videopath, fourcc, fps, (width, height), True)
  if not handle.isOpened():
    raise Exception('video failed to open: %s' % videopath)
  return handle



parser = argparse.ArgumentParser()
parser.add_argument('--in_files', nargs='+', required=True,
                    help='paths to video files relative to "relpath"')
parser.add_argument('--tags', nargs='+',
                    help='name to overlay on each video. Default is no tag')
parser.add_argument('--out_file', required=True,
                    help='path to output video file relative to "relpath"')
parser.add_argument('--relpath', default=os.getenv('CITY_DATA_PATH'))
parser.add_argument('--grid_X',        type=int, required=True)
parser.add_argument('--grid_Y',        type=int, required=True)
parser.add_argument('--width',         type=int)
parser.add_argument('--height',        type=int)
parser.add_argument('--pad_to_ratio',  type=float,
                    help='H / W. Pad with white everything around')
parser.add_argument('--pad',           type=int, default=10)
parser.add_argument('--num_frames',    type=int, default=10000000,
                    help='default is until one of the input videos ends')
parser.add_argument('--debug_show', action='store_true')
args = parser.parse_args()
assert not args.tags or len(args.in_files) == len(args.tags)

hs = []
for in_file in args.in_files:
  h = _openVideoCapture_ (op.join(args.relpath, in_file), relpath=args.relpath)
  hs.append(h)

# lazy initialization
hout = None
frame_size = None
empty_img = None

start_time = time.time()

for i in range(args.num_frames):
  if i % 100 == 0: 
    print ('%d sec: step %d' % (time.time() - start_time, i))

  # check if any video ended
  do_break = False
  imgs = []
  for i,h in enumerate(hs):
    retval, img = h.read()
    if not retval: 
      do_break=True
      print ('video #%d ended' % i)
    imgs.append(img)
  if do_break: break

  if frame_size is None:
    # init frame_size
    if args.width and args.height: 
      frame_size = (args.width, args.height)
    else:
      frame_size = img.shape[:2]
    # init empty_img
    empty_img = np.ones((frame_size[1],frame_size[0],3), dtype=np.uint8) * 255

  imgs_rows = []
  for y in range(args.grid_Y):
    imgs_row = []
    for x in range(args.grid_X):
      i = y*args.grid_X+x
      img = imgs[i] if i < len(imgs) else empty_img
      img = cv2.resize(img, frame_size)
      p = args.pad
      img = np.pad(img, ((p,0),(p,0),(0,0)), 'constant', constant_values=255)
      if args.tags and i < len(args.tags):
        cv2.rectangle(img, (0,0), (400,30), (0,0,0), cv2.cv.CV_FILLED)
        cv2.putText(img, args.tags[i], (0,26), cv2.FONT_HERSHEY_PLAIN, 2, (0,255,0), 2)
      imgs_row.append(img)
    imgs_rows.append (np.hstack(tuple(imgs_row)))
  img_out = np.vstack(tuple(imgs_rows))

  # to target_ratio
  if args.pad_to_ratio is not None:
    if img_out.shape[1] * args.pad_to_ratio > img_out.shape[0]:
      p = int(img_out.shape[1] * args.pad_to_ratio - img_out.shape[0]) / 2
      img_out = np.pad(img_out, ((p,p),(0,0),(0,0)), 'constant', constant_values=255)
    else:
      p = int(img_out.shape[0] / args.pad_to_ratio - img_out.shape[1]) / 2
      img_out = np.pad(img_out, ((0,0),(p,p),(0,0)), 'constant', constant_values=255)

  if hout is None:
    # init hout
    out_size = (img_out.shape[1], img_out.shape[0])
    hout = _openVideoWriter_(op.join(args.relpath, args.out_file), 
                             hs[0], out_size, relpath=args.relpath)
  assert out_size == (img_out.shape[1], img_out.shape[0])
  hout.write(img_out)

  if args.debug_show:
    cv2.imshow ("test", img_out)
    if cv2.waitKey(-1) == 27: break

hout.release()