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

    # check out_image_dir
    if op.exists (out_image_dir):
        shutil.rmtree(out_image_dir)
    os.makedirs (out_image_dir)

    # create and empty db
    conn = sqlite3.connect(out_db_path)
    helperDb.createDbFromConn(conn)
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
