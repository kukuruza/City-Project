import numpy as np
import cv2
import os, sys
import os.path as op
import logging
import sqlite3
import helperSetup
import helperDb
import helperImg


def video2database (in_video_path, out_image_dir, out_db_path, params):
    '''
    Take a video and make a database out of it
    '''

    # FIXME: process timestamps

    logging.info ('==== video2database ====')
    helperSetup.setParamUnlessThere (params, 'src', '')
    helperSetup.setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
    helperSetup.setParamUnlessThere (params, 'image_processor', helperImg.ProcessorImagefile())

    in_video_path = op.join(params['relpath'], in_video_path)
    if not op.exists (in_video_path):
        raise Exception ('video does not exist: %s' + in_video_path)

    # create and empty db
    os.makedirs (op.dirname(out_db_path))
    conn = sqlite3.connect(out_db_path)
    helperDb.createDb(conn)
    c = conn.cursor()

    video = cv2.VideoCapture(in_video_path)
    counter = 0
    while (True):
        ret, frame = video.read()
        if not ret: break

        # write image
        imagefile = op.join(out_image_dir, '%06d.jpg' % counter)
        params['image_processor'].imwrite(frame, imagefile)

        # write .db entry
        (w,h) = frame.shape[0:2]
        s = 'images(imagefile,src,width,height)'
        c.execute ('INSERT INTO %s VALUES (?,?,?,?)' % s, (imagefile, params['src'], w, h))

        counter += 1

    conn.commit()
    conn.close()



def video2dataset (videos_prefix, dataset_dir, dataset_name, params = {}):
    ''' 
    Build a dataset based on videos 'frame' (source), 'ghost' and 'mask', as well as timestamp .txt
    The format may change over time.
    '''
    logging.info ('==== videos2dataset ====')
    helperSetup.setParamUnlessThere (params, 'frame_suffix', '.avi')
    helperSetup.setParamUnlessThere (params, 'ghost_suffix', '-ghost.avi')
    helperSetup.setParamUnlessThere (params, 'mask_suffix',  '-mask.avi')
    helperSetup.setParamUnlessThere (params, 'time_suffix',  '.txt')
    helperSetup.setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
    helperSetup.setParamUnlessThere (params, 'image_processor', helperImg.ProcessorImagefile())

    # datasets for images, ghosts, and masks
    database_dir   = op.join (dataset_dir, 'databases', dataset_name)
    dataset_images = op.join (dataset_dir, 'images',    dataset_name)
    dataset_ghosts = op.join (dataset_dir, 'ghosts',    dataset_name)
    dataset_masks  = op.join (dataset_dir, 'masks',     dataset_name)

    # create and empty db-s
    os.makedirs (op.join(params['relpath'], database_dir))
    conn_frame = sqlite3.connect (op.join(params['relpath'], database_dir, 'init-image.db'))
    conn_ghost = sqlite3.connect (op.join(params['relpath'], database_dir, 'init-ghost.db'))
    helperDb.createDb(conn_frame)
    helperDb.createDb(conn_ghost)
    c_frame = conn_frame.cursor()
    c_ghost = conn_ghost.cursor()

    # read timestamps
    with open(op.join(params['relpath'], videos_prefix, params['time_suffix'])) as f:
        timestamps = f.readlines()

    # open all videos
    frameVideo = cv2.VideoCapture (op.join(params['relpath'], videos_prefix, params['frame_suffix']))
    ghostVideo = cv2.VideoCapture (op.join(params['relpath'], videos_prefix, params['ghost_suffix']))
    maskVideo  = cv2.VideoCapture (op.join(params['relpath'], videos_prefix, params['mask_suffix']))

    while (True):
        ret1, frame = frameVideo.read()
        ret2, ghost = ghostVideo.read()
        ret3, mask  = maskVideo.read()
        if not (ret1 and ret2 and ret3) and not (not ret1 and not ret2 and not ret3):
            raise ('videos2dataset: videos are of different length')
        if not ret1: break

        # write image, ghost, and mask
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        framefile = op.join (dataset_frames, '%06d.jpg' % counter)
        ghostfile = op.join (dataset_ghosts, '%06d.jpg' % counter)
        maskfile  = op.join (dataset_masks,  '%06d.png' % counter)
        params['image_processor'].imwrite (frame, framepath)
        params['image_processor'].imwrite (ghost, ghostfile)
        params['image_processor'].imwrite (mask, maskfile)

        # write .db entry
        (w,h) = frame.shape[0:2]
        s = 'images(imagefile,maskfile,src,width,height)'
        c_frame.execute ('INSERT INTO %s VALUES (?,?,?,?,?)' % s, (imagefile,maskfile,dataset_name,w,h))
        c_ghost.execute ('INSERT INTO %s VALUES (?,?,?,?,?)' % s, (ghostfile,maskfile,dataset_name,w,h))

        counter += 1

    conn_frame.commit()
    conn_ghost.commit()
    conn_frame.close()
    conn_ghost.close()

    
