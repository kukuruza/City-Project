#
# This script collects negative training samples from images
# It uses clusters.json file for information about filters
#
# Assumptions are: 1) all cars are labelled in each image (maybe several times)
#

import numpy as np
import numpy.ma as ma
import cv2
import os, sys
import collections
import logging
import json
import os.path as op
import glob
import shutil
import sqlite3
from dbInterface import deleteCar, queryField, queryCars
from utilities import bbox2roi, getCenter, __setParamUnlessThere__



def __grayCircle__ (cursor, (imagefile, ghostfile), filter_group, out_dir, params = {}):

    params = __setParamUnlessThere__ (params, 'spot_scale', 0.6)

    ghostpath = op.join (os.getenv('CITY_DATA_PATH'), ghostfile)
    if not op.exists (ghostpath):
        raise Exception ('ghost does not exist: ' + ghostpath)
    ghost = cv2.imread(ghostpath)

    filter_group['imagefile'] = imagefile
    car_entries = queryCars (cursor, filter_group)
    logging.debug (str(len(car_entries)) + ' objects found for "' + 
                   filter_group['filter'] + '" in ' + imagefile)

    for car_entry in car_entries:
        bbox = queryField(car_entry, 'bbox-w-offset')
        spot_scale = params['spot_scale']
        axes = (int(bbox[2] * spot_scale / 2), int(bbox[3] * spot_scale / 2))
        (cy, cx) = getCenter(bbox2roi(bbox))
        cv2.ellipse (ghost, (cx, cy), axes, 0, 0, 360, (128,128,128), -1)

    cv2.imwrite (op.join(out_dir, op.basename(ghostfile)), ghost)



def __grayMasked__ (cursor, (imagefile, ghostfile), filter_group, out_dir, params = {}):

    params = __setParamUnlessThere__ (params, 'dilate', 1. / 4)
    params = __setParamUnlessThere__ (params, 'erode', 1. / 2.5)

    if not 'width' in filter_group.keys():
        raise Exception ('no width in filter_group')

    ghostpath = op.join (os.getenv('CITY_DATA_PATH'), ghostfile)
    if not op.exists (ghostpath):
        raise Exception ('ghost does not exist: ' + ghostpath)
    ghost = cv2.imread(ghostpath)

    filter_group['imagefile'] = imagefile
    car_entries = queryCars (cursor, filter_group)
    logging.debug (str(len(car_entries)) + ' objects found for "' + 
                   filter_group['filter'] + '" in ' + imagefile)

    cursor.execute ('SELECT maskfile FROM images WHERE imagefile = ?', (imagefile,))
    (maskfile,) = cursor.fetchone()
    maskpath = op.join (os.getenv('CITY_DATA_PATH'), maskfile)
    mask = cv2.imread(maskpath).astype(np.uint8)
    sz_dilate = int(filter_group['width'] * params['dilate'])
    sz_erode  = int(filter_group['width'] * params['erode'])
    mask = cv2.dilate (mask, np.ones((sz_dilate, sz_dilate), 'uint8'))
    mask = cv2.erode  (mask, np.ones((sz_erode, sz_erode), 'uint8'))
    mask = mask.astype(np.bool)

    ghost[mask] = 128

    cv2.imwrite (op.join(out_dir, op.basename(ghostfile)), ghost)



def negativeGrayspots (db_path, filters_path, out_dir, params = {}):

    params = __setParamUnlessThere__ (params, 'method', 'circle')

    logging.info ('=== negativeGrayspots ===')
    logging.info ('called with db_path: ' + db_path)
    logging.info ('            filters_path: ' + filters_path)
    logging.info ('            out_dir: ' + out_dir)
    logging.info ('            params: ' + str(params))

    # check output dir
    if not op.exists (out_dir):
        os.makedirs (out_dir)

    # check input db
    if not op.exists (db_path):
        raise Exception ('db does not exist: ' + db_path)

    # load clusters
    if not op.exists(filters_path):
        raise Exception('filters_path does not exist: ' + filters_path)
    filters_file = open(filters_path)
    filters_groups = json.load(filters_file)
    filters_file.close()

    conn = sqlite3.connect (db_path)
    cursor = conn.cursor()

    for filter_group in filters_groups:
        assert ('filter' in filter_group)
        logging.info ('filter group ' + filter_group['filter'])

        # delete and re-create a dir for a cluster
        cluster_dir = op.join (out_dir, filter_group['filter'])
        if op.exists (cluster_dir):
            logging.warning ('will delete existing cluster dir: ' + cluster_dir)
            shutil.rmtree (cluster_dir)
        os.makedirs (cluster_dir)

        cursor.execute('SELECT imagefile, ghostfile FROM images')
        image_entries = cursor.fetchall()

        for (imagefile, ghostfile) in image_entries:
            if params['method'] == 'circle':
                __grayCircle__ (cursor, (imagefile, ghostfile), filter_group, cluster_dir, params)
            elif params['method'] == 'mask':
                __grayMasked__ (cursor, (imagefile, ghostfile), filter_group, cluster_dir, params)
            else:
                raise Exception ('can not recognize method: ' + params['method'])

    conn.close()

    # write info
    with open(op.join(out_dir, 'readme.txt'), 'w') as readme:
        readme.write('from database ' + db_path + '\n')
        readme.write('with filters  ' + filters_path + '\n')


