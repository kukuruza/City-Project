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



def _openVideo_ (videopath, params)
    ''' Open video and set up bookkeeping '''
    logging.info ('opening video: %s' % videopath)
    videopath = op.join (params['relpath'], videopath)
    if not op.exists (videopath):
        raise Exception('videopath does not exist: %s' % videopath)
    handle = cv2.VideoCapture(videopath)  # open video
    if not handle.isOpened():
        raise Exception('video failed to open: %s' % videopath)
    return handle


def initFromVideo (cursor, image_video_path, mask_video_path, time_path, params):
    helperSetup.setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
    helperSetup.setParamUnlessThere (params, 'name', op.basename(op.dirname(image_video_path)))

    image_video = _openVideo_(image_video_path, params)
    mask_video  = _openVideo_(mask_video_path, params)

    width     = int(image_video.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH))
    height    = int(image_video.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
    numframes = int(image_video.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT))
    assert (width     = int(mask_video.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)))
    assert (height    = int(mask_video.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)))
    assert (numframes = int(mask_video.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)))

    # read timestamps
    with open(op.join(params['relpath'], time_path)) as f:
        timestamps = f.readlines()

    for i in range(numframes):
        imagefile = op.join (image_video_path, '%06d' % i)
        maskfile  = op.join (mask_video_path,  '%06d' % i)
        timestamp = timestamps[i]
        s = 'images(imagefile,maskfile,src,width,height,time)'
        cursor.execute('INSERT INTO %s VALUES (?,?,?,?,?,?)' % s, \
            (imagefile,maskfile,name,width,height,timestamp))






def _video2dataset_ (c, image_video_path, mask_video_path, time_path, image_dir, mask_dir, name, params):
    '''
    Take a video of 'images' and 'masks' and make a dataset out of it
    '''
    logging.info ('==== video2dataset ====')
    helperSetup.setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
    helperSetup.setParamUnlessThere (params, 'image_processor', helperImg.ReaderVideo(params))

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
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        imagefile = op.join (image_dir, '%06d.jpg' % counter)
        maskfile  = op.join (mask_dir,  '%06d.png' % counter)
        params['image_processor'].imwrite (frame, imagefile)
        params['image_processor'].maskwrite (mask, maskfile)

        # get and validate time
        timestamp = timestamps[counter].rstrip()
        try:
            datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            raise ValueError('incorrect time "%s", expected YYYY-MM-DD HH-MM-SS.ffffff' % timestamp)

        # write .db entry
        (w,h) = frame.shape[0:2]
        s = 'images(imagefile,maskfile,src,width,height,time)'
        c.execute ('INSERT INTO %s VALUES (?,?,?,?,?,?)' % s, (imagefile,maskfile,name,w,h,timestamp))

        counter += 1



def makeDataset (videos_prefix, dataset_dir, dataset_name, params = {}):
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

    # datasets for images, ghosts, and masks
    image_dir = op.join (dataset_dir, 'images',    dataset_name)
    ghost_dir = op.join (dataset_dir, 'ghosts',    dataset_name)
    mask_dir  = op.join (dataset_dir, 'masks',     dataset_name)
    db_dir    = op.join (dataset_dir, 'databases', dataset_name)
    db_dir    = op.join (params['relpath'], db_dir)

    # create and empty db-s
    if not op.exists(db_dir): os.makedirs (db_dir)
    conn_frame = sqlite3.connect (op.join(db_dir, 'init-image.db'))
    conn_ghost = sqlite3.connect (op.join(db_dir, 'init-ghost.db'))
    helperDb.createDb(conn_frame)
    helperDb.createDb(conn_ghost)
    c_frame = conn_frame.cursor()
    c_ghost = conn_ghost.cursor()

    _video2dataset_ (c_frame, image_video_path, mask_video_path, time_path, 
                     ghost_dir, mask_dir, dataset_name, params)
    _video2dataset_ (c_frame, ghost_video_path, mask_video_path, time_path, 
                     image_dir, mask_dir, dataset_name, params)

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


