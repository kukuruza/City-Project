import os, sys, os.path as op
import numpy as np
import cv2
import logging
import sqlite3
import datetime
import traceback
from helperSetup import atcity, _setupCopyDb_, setParamUnlessThere, assertParamIsThere
from helperDb    import createDb, carField, makeTimeString
from dbUtilities import bbox2roi, drawScoredRoi



def video2dataset (c, image_video_file, mask_video_file, time_file, name, params = {}):
    '''
    Take a video of 'images' and 'masks' and make a dataset out of it
    Args:
      time_file:  if None, null values will be written to db
    '''
    logging.info ('==== video2dataset ====')
    setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))

    logging.info ('image file: %s' % image_video_file)
    logging.info ('mask file:  %s' % mask_video_file)
    logging.info ('time file:  %s' % time_file)

    # test the full video paths
    if not op.exists (op.join(params['relpath'], image_video_file)):
        raise Exception ('image video does not exist: %s' % image_video_file)
    if mask_video_file is not None and \
       not op.exists (op.join(params['relpath'], mask_video_file)):
        logging.warning ('mask video does not exist: %s' % mask_video_file)
        mask_video_file = None

    imageVideo = cv2.VideoCapture (op.join(params['relpath'], image_video_file))
    #maskVideo  = cv2.VideoCapture (op.join(params['relpath'], mask_video_file))

    # read timestamps
    if time_file is not None:
        with open(op.join(params['relpath'], time_file)) as f:
            timestamps = f.readlines()

    counter = 0
    while (True):
        ret1, frame = imageVideo.read()
        #ret2, mask  = maskVideo.read()
        #if not (ret1 and ret2) and not (not ret1 and not ret2):
        #    logging.error ('ret1: %d, ret2: %d' % (ret1, ret2))
        #    raise Exception('video2dataset: videos are of different length')
        if not ret1: break

        # write image, ghost, and mask
        imagefile = op.join (op.splitext(image_video_file)[0], '%06d' % counter)
        if mask_video_file is None:
            maskfile = None
        else:
            maskfile  = op.join (op.splitext(mask_video_file)[0],  '%06d' % counter)

        # get and validate time
        if time_file is None:
            timestamp = None
        else:
            timestamp = timestamps[counter].rstrip()
            try:
                datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                raise ValueError('incorrect time "%s", expected YYYY-MM-DD HH:MM:SS.ffffff' % timestamp)

        # write .db entry
        (h,w) = frame.shape[0:2]
        s = 'images(imagefile,maskfile,src,width,height,time)'
        c.execute ('INSERT INTO %s VALUES (?,?,?,?,?,?)' % s, (imagefile,maskfile,name,w,h,timestamp))

        counter += 1



def make_dataset (video_dir, db_file, params = {}):
    ''' 
    Build a dataset based on videos 'frame' (source), 'ghost' and 'mask', as well as timestamp .txt
    The format may change over time.
    '''
    logging.info ('==== make_dataset ====')
    setParamUnlessThere (params, 'image_video_name', 'src.avi')
    setParamUnlessThere (params, 'mask_video_name', 'mask.avi')

    # take care of dir and name of the db
    db_dir = op.dirname(atcity(db_file))
    logging.info ('db_dir: %s' % db_dir)
    if not op.exists(db_dir): 
        os.makedirs (db_dir)
    db_name = op.basename(db_file)

    # form video and time paths
    video_file = op.join(video_dir, params['image_video_name'])
    mask_file  = op.join(video_dir, params['mask_video_name'])
    time_file  = op.join(video_dir, 'time.txt')

    db_path = atcity(db_file)
    assert op.exists(op.dirname(db_path)), db_path
    print db_path
    conn = sqlite3.connect(db_path)
    createDb(conn)
    c = conn.cursor()
    video2dataset (c, video_file, mask_file, time_file, db_name, params)
    conn.commit()
    conn.close()
    logging.info ('successfully made a db from %s' % video_file)
