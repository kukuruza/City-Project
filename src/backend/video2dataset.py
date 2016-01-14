import os, sys, os.path as op
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/backend'))
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
import numpy as np
import cv2
import logging
import sqlite3
import datetime
import helperSetup
import helperDb
import helperImg
import utilities



def video2dataset (c, image_video_path, mask_video_path, time_path, name, params = {}):
    '''
    Take a video of 'images' and 'masks' and make a dataset out of it
    '''
    logging.info ('==== video2dataset ====')
    helperSetup.setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))

    logging.info ('image path: %s' % image_video_path)
    logging.info ('mask path:  %s' % mask_video_path)
    logging.info ('time path:  %s' % time_path)

    # get the full video paths
    if not op.exists (op.join(params['relpath'], image_video_path)):
        raise Exception ('image video does not exist: %s' % image_video_path)
    if not op.exists (op.join(params['relpath'], mask_video_path)):
        raise Exception ('mask video does not exist: %s' % mask_video_path)

    # read timestamps
    with open(op.join(params['relpath'], time_path)) as f:
        timestamps = f.readlines()

    imageVideo = cv2.VideoCapture (op.join(params['relpath'], image_video_path))
    maskVideo  = cv2.VideoCapture (op.join(params['relpath'], mask_video_path))

    counter = 0
    while (True):
        ret1, frame = imageVideo.read()
        ret2, mask  = maskVideo.read()
        if not (ret1 and ret2) and not (not ret1 and not ret2):
            logging.error ('ret1: %d, ret2: %d' % (ret1, ret2))
            raise Exception('video2dataset: videos are of different length')
        if not ret1: break

        # write image, ghost, and mask
        imagefile = op.join (op.splitext(image_video_path)[0], '%06d' % counter)
        maskfile  = op.join (op.splitext(mask_video_path)[0],  '%06d' % counter)

        # get and validate time
        timestamp = timestamps[counter].rstrip()
        try:
            datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            raise ValueError('incorrect time "%s", expected YYYY-MM-DD HH-MM-SS.ffffff' % timestamp)

        # write .db entry
        (h,w) = frame.shape[0:2]
        s = 'images(imagefile,maskfile,src,width,height,time)'
        c.execute ('INSERT INTO %s VALUES (?,?,?,?,?,?)' % s, (imagefile,maskfile,name,w,h,timestamp))

        counter += 1



def makeDataset (videos_prefix, db_prefix, params = {}):
    ''' 
    Build a dataset based on videos 'frame' (source), 'ghost' and 'mask', as well as timestamp .txt
    The format may change over time.
    '''
    logging.info ('==== makeDataset ====')
    helperSetup.setParamUnlessThere (params, 'image_suffix', '.avi')
    helperSetup.setParamUnlessThere (params, 'ghost_suffix', '-ghost.avi')
    helperSetup.setParamUnlessThere (params, 'mask_suffix',  '-mask.avi')
    helperSetup.setParamUnlessThere (params, 'time_suffix',  '.txt')
    helperSetup.setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
    helperSetup.setParamUnlessThere (params, 'image_processor', helperImg.ReaderVideo(params))

    # form video and time paths
    image_video_path = op.join(videos_prefix + params['image_suffix'])
    ghost_video_path = op.join(videos_prefix + params['ghost_suffix'])
    mask_video_path  = op.join(videos_prefix + params['mask_suffix'])
    time_path        = op.join(videos_prefix + params['time_suffix'])

    # create and empty db-s
    db_dir = op.dirname(op.join(params['relpath'], db_prefix))
    logging.info ('db_dir: %s' % db_dir)
    if not op.exists(db_dir): os.makedirs (db_dir)
    conn_frame = sqlite3.connect (op.join(params['relpath'], '%s-image.db' % db_prefix))
    conn_ghost = sqlite3.connect (op.join(params['relpath'], '%s-ghost.db' % db_prefix))
    helperDb.createDb(conn_frame)
    helperDb.createDb(conn_ghost)
    c_frame = conn_frame.cursor()
    c_ghost = conn_ghost.cursor()

    db_name = op.basename(db_prefix)
    video2dataset (c_frame, image_video_path, mask_video_path, time_path, db_name, params)
    video2dataset (c_ghost, ghost_video_path, mask_video_path, time_path, db_name, params)

    conn_frame.commit()
    conn_ghost.commit()
    conn_frame.close()
    conn_ghost.close()

    

def exportVideo (c, params = {}):
    logging.info ('==== exportVideo ====')
    helperSetup.setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
    helperSetup.assertParamIsThere  (params, 'image_processor')

    c.execute('SELECT imagefile FROM images')
    for (imagefile,) in c.fetchall():

        frame = params['image_processor'].imread(imagefile)

        c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
        for car_entry in c.fetchall():
            roi       = utilities.bbox2roi (helperDb.carField(car_entry, 'bbox'))
            imagefile = helperDb.carField (car_entry, 'imagefile')
            name      = helperDb.carField (car_entry, 'name')
            score     = helperDb.carField (car_entry, 'score')

            if score is None: score = 1
            logging.debug ('roi: %s, score: %f' % (str(roi), score))
            utilities.drawScoredRoi (frame, roi, name, score)

        params['image_processor'].imwrite(frame, imagefile)


