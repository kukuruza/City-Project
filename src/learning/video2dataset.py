import os, sys, os.path as op
import numpy as np
import cv2
import logging
import sqlite3
import datetime
import traceback
from helperSetup import atcity, _setupCopyDb_, setParamUnlessThere, assertParamIsThere
from helperDb    import createDb, carField
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
    if not op.exists (op.join(params['relpath'], mask_video_file)):
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



def make_dataset (video_dir, db_prefix, params = {}):
    ''' 
    Build a dataset based on videos 'frame' (source), 'ghost' and 'mask', as well as timestamp .txt
    The format may change over time.
    '''
    logging.info ('==== make_dataset ====')
    setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
    setParamUnlessThere (params, 'videotypes', ['src', 'ghost'])

    # take care of dir and name of the db
    db_dir = op.dirname(op.join(params['relpath'], db_prefix))
    logging.info ('db_dir: %s' % db_dir)
    if not op.exists(db_dir): 
        os.makedirs (db_dir)
    db_name = op.basename(op.dirname(db_prefix))

    for videotype in params['videotypes']:

        # form video and time paths
        video_file = op.join(video_dir, '%s.avi' % videotype)
        mask_file  = op.join(video_dir, 'mask.avi')
        time_file  = op.join(video_dir, 'time.txt')

        db_path = op.join(params['relpath'], '%s-%s.db' % (db_prefix, videotype))
        conn = sqlite3.connect(db_path)
        createDb(conn)
        c = conn.cursor()
        video2dataset (c, video_file, mask_video_file, time_file, db_name, params)
        conn.commit()
        conn.close()
        logging.info ('successfully made a db from %s' % video_file)


    

def exportVideo (c, params = {}):
    logging.info ('==== exportVideo ====')
    setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
    assertParamIsThere  (params, 'image_processor')

    c.execute('SELECT imagefile FROM images')
    for (imagefile,) in c.fetchall():

        frame = params['image_processor'].imread(imagefile)

        c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
        for car_entry in c.fetchall():
            roi       = bbox2roi (carField(car_entry, 'bbox'))
            imagefile = carField (car_entry, 'imagefile')
            name      = carField (car_entry, 'name')
            score     = carField (car_entry, 'score')

            if score is None: score = 1
            logging.debug ('roi: %s, score: %f' % (str(roi), score))
            drawScoredRoi (frame, roi, name, score)

        params['image_processor'].imwrite(frame, imagefile)


