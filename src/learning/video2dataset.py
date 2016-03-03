import os, sys, os.path as op
import numpy as np
import cv2
import logging
import sqlite3
import datetime
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
        raise Exception ('mask video does not exist: %s' % mask_video_file)

    # read timestamps
    if time_file is not None:
        with open(op.join(params['relpath'], time_file)) as f:
            timestamps = f.readlines()

    imageVideo = cv2.VideoCapture (op.join(params['relpath'], image_video_file))
    maskVideo  = cv2.VideoCapture (op.join(params['relpath'], mask_video_file))

    counter = 0
    while (True):
        ret1, frame = imageVideo.read()
        ret2, mask  = maskVideo.read()
        if not (ret1 and ret2) and not (not ret1 and not ret2):
            logging.error ('ret1: %d, ret2: %d' % (ret1, ret2))
            raise Exception('video2dataset: videos are of different length')
        if not ret1: break

        # write image, ghost, and mask
        imagefile = op.join (op.splitext(image_video_file)[0], '%06d' % counter)
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

    # form video and time paths
    image_video_file = op.join(video_dir, 'src.avi')
    ghost_video_file = op.join(video_dir, 'ghost.avi')
    mask_video_file  = op.join(video_dir, 'mask.avi')
    time_file        = op.join(video_dir, 'time.txt')

    # create and empty db-s
    db_dir = op.dirname(op.join(params['relpath'], db_prefix))
    logging.info ('db_dir: %s' % db_dir)
    if not op.exists(db_dir): os.makedirs (db_dir)
    conn_frame = sqlite3.connect (op.join(params['relpath'], '%s-image.db' % db_prefix))
    conn_ghost = sqlite3.connect (op.join(params['relpath'], '%s-ghost.db' % db_prefix))
    createDb(conn_frame)
    createDb(conn_ghost)
    c_frame = conn_frame.cursor()
    c_ghost = conn_ghost.cursor()

    db_name = op.basename(db_prefix)
    video2dataset (c_frame, image_video_file, mask_video_file, time_file, db_name, params)
    video2dataset (c_ghost, ghost_video_file, mask_video_file, time_file, db_name, params)

    conn_frame.commit()
    conn_ghost.commit()
    conn_frame.close()
    conn_ghost.close()



def make_back_dataset (video_dir, out_db_file, params = {}):
    ''' 
    Build a dataset based on 'back' and 'mask' videos, as well as timestamp .txt
    The format may change over time.
    '''
    logging.info ('==== make_back_dataset ====')
    setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))

    # form video and time paths
    back_video_file  = op.join(video_dir, 'back.avi')
    mask_video_file  = op.join(video_dir, 'mask.avi')
    time_file        = op.join(video_dir, 'time.txt')

    # form db name
    camera_name = op.basename(op.dirname(video_dir))
    video_name  = op.basename(video_dir)
    name = '%s-%s' % (camera_name, video_name)

    # create parent dir and remove the previous file, if exists
    if not op.exists(atcity(op.dirname(out_db_file))): 
        os.makedirs (atcity(op.dirname(out_db_file)))
    if op.exists(atcity(out_db_file)):
        os.remove(atcity(out_db_file))

    conn = sqlite3.connect(atcity(out_db_file))
    createDb(conn)
    c = conn.cursor()

    video2dataset (c, back_video_file, mask_video_file, time_file, name)

    conn.commit()
    conn.close()

    

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


