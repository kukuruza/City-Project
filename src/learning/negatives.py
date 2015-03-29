#
# This script collects negative training samples from images
# It uses clusters.json file for information about filters
#
# Assumptions are: 1) all cars are labelled in each image (maybe several times)
#

import numpy as np
import cv2
import os, sys
import collections
import logging
import json
import os.path as op
import glob
import shutil
import sqlite3
import random
from dbInterface import deleteCar, queryField, queryCars
from utilities import bbox2roi, getCenter
from setup_helper import setParamUnlessThere, get_CITY_DATA_PATH

IMAGE_EXT = '.png'


def __grayCircle__ (cursor, (imagefile, ghostfile), filter_group, out_dir, params = {}):

    params = setParamUnlessThere (params, 'spot_scale', 0.6)

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

    params = setParamUnlessThere (params, 'dilate', 1. / 4)
    params = setParamUnlessThere (params, 'erode', 1. / 2.5)

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

    CITY_DATA_PATH = get_CITY_DATA_PATH()
    db_path      = op.join(CITY_DATA_PATH, db_path)
    filters_path = op.join(CITY_DATA_PATH, filters_path)
    out_dir      = op.join(CITY_DATA_PATH, out_dir)

    params = setParamUnlessThere (params, 'method', 'circle')

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



def __getPatchesFromImage__ (imagepath, num, params):

    #logging.debug ('farming patches from ' + imagepath)
    if not op.exists (imagepath):
        raise Exception ('imagepath does not exist: ' + imagepath)

    img = cv2.imread(imagepath).astype(np.uint8)
    assert (img is not None)
    (im_height, im_width, depth) = img.shape

    if 'mask' not in params.keys():
        params['mask'] = np.zeros(img.shape, dtype = np.uint8)

    patches = []
    counter = 0
    for i in range (num * 100):

        # randomly select x1, y1, width; calculate height; and extract the patch
        patch_width = random.randint (params['minwidth'], params['maxwidth'])
        patch_height = int(patch_width * params['ratio'])
        if im_width < patch_width or im_height < patch_height:
            continue
        x1 = random.randint (0, im_width - patch_width)
        y1 = random.randint (0, im_height - patch_height)
        patch = img[y1:y1+patch_height, x1:x1+patch_width, :]

        # check if patch is within the mask
        masked = params['mask'][y1:y1+patch_height, x1:x1+patch_width, :]
        masked_perc = float(np.count_nonzero(masked)) / masked.size
        if masked_perc > params['max_masked_perc']:
            logging.debug ('masked_perc ' + '%.2f' % masked_perc + ' above limit')
            continue

        patch = cv2.resize(patch, tuple(params['resize']))
        patches.append(patch)

        if counter >= num: break
        counter += 1

    logging.info (op.basename(imagepath) + ': got ' + str(len(patches)) + ' patches')
    return patches



def negativeViaMaskfiles (db_path, filters_path, out_dir, params = {}):

    logging.info ('=== negativeGrayspots ===')
    logging.info ('called with db_path: ' + db_path)
    logging.info ('            filters_path: ' + filters_path)
    logging.info ('            out_dir: ' + out_dir)
    logging.info ('            params: ' + str(params))

    CITY_DATA_PATH = get_CITY_DATA_PATH()
    db_path      = op.join(CITY_DATA_PATH, db_path)
    filters_path = op.join(CITY_DATA_PATH, filters_path)
    out_dir      = op.join(CITY_DATA_PATH, out_dir)

    params = setParamUnlessThere (params, 'method', 'circle')
    params = setParamUnlessThere (params, 'number', 100)
    params = setParamUnlessThere (params, 'ratio', 0.75)
    params = setParamUnlessThere (params, 'minwidth', 20)
    params = setParamUnlessThere (params, 'maxwidth', 200)
    params = setParamUnlessThere (params, 'max_masked_perc', 0.5)
    params = setParamUnlessThere (params, 'debug_mask', False)

    # check output dir
    if op.exists (out_dir):
        shutil.rmtree(out_dir)
    os.makedirs (out_dir)

    random.seed()

    # check input db
    if not op.exists (db_path):
        raise Exception ('db does not exist: ' + db_path)

    random.seed()

    conn = sqlite3.connect (db_path)
    cursor = conn.cursor()

    # if given, size_map will serve as mask too
    if 'size_map_path' in params.keys():
        size_map_path  = op.join(CITY_DATA_PATH, params['size_map_path'])
        logging.info ('will load size_map from: ' + size_map_path)
        if not op.exists (size_map_path):
            raise Exception ('size_map_path does not exist: ' + size_map_path)
        size_map = cv2.imread (size_map_path)
        assert (size_map is not None)
        size_mask = (size_map == 0)
    else:
        cursor.execute('SELECT width,height FROM images')
        (width,height) = cursor.fetchone()
        size_mask = np.zeros ((width,height), dtype=bool)
    if params['debug_mask']:
        cv2.imshow('size_mask', size_mask.astype(np.uint8) * 255)
        cv2.waitKey()

    cursor.execute('SELECT ghostfile, maskfile FROM images')
    image_entries = cursor.fetchall()
    random.shuffle(image_entries)
    if not image_entries:
        raise Exception ('no image found in db')
    logging.info ('found ' + str(len(image_entries)) + ' in in_dir')
    num_per_image = int(params['number'] / len(image_entries)) + 1

    conn.close()

    counter = 0
    for (ghostfile, maskfile) in image_entries:
        ghostpath = op.join(CITY_DATA_PATH, ghostfile)
        maskpath  = op.join(CITY_DATA_PATH, maskfile)
        immask = cv2.imread (maskpath)
        assert (immask is not None)
        params['mask'] = np.logical_or (size_mask, immask)
        if params['debug_mask']:
            cv2.imshow('combined mask', params['mask'].astype(np.uint8) * 255)
            cv2.waitKey()

        for patch in __getPatchesFromImage__(ghostpath, num_per_image, params):
            filename = "%08d" % counter + IMAGE_EXT
            filepath = op.join(out_dir, filename)
            cv2.imwrite (filepath, patch)
            counter += 1
            if counter >= params['number']: return

    if counter < params['number']:
        logging.error ('got only ' + str(counter) + ' patches')



def negativeImages2patches (in_dir, out_dir, params = {}):

    logging.info ('=== negativeGrayspots ===')
    logging.info ('called with in_dir: ' + in_dir)
    logging.info ('            out_dir: ' + out_dir)
    logging.info ('            params: ' + str(params))

    CITY_DATA_PATH = get_CITY_DATA_PATH()
    in_dir       = op.join(CITY_DATA_PATH, in_dir)
    out_dir      = op.join(CITY_DATA_PATH, out_dir)

    params = setParamUnlessThere (params, 'number', 100)
    params = setParamUnlessThere (params, 'ratio', 0.75)
    params = setParamUnlessThere (params, 'minwidth', 20)
    params = setParamUnlessThere (params, 'maxwidth', 200)
    params = setParamUnlessThere (params, 'max_masked_perc', 0.5)
    params = setParamUnlessThere (params, 'ext', '.jpg')
    params = setParamUnlessThere (params, 'debug_mask', False)

    if 'size_map_path' in params.keys():
        size_map_path  = op.join(CITY_DATA_PATH, params['size_map_path'])
        logging.info ('will load size_map from: ' + size_map_path)
        if not op.exists (size_map_path):
            raise Exception ('size_map_path does not exist: ' + size_map_path)
        size_map = cv2.imread (size_map_path)
        assert (size_map is not None)
        params['mask'] = (size_map == 0)
        if params['debug_mask']:
            cv2.imshow('size_map mask', params['mask'])
            cv2.waitKey()

    # check output dir
    if op.exists (out_dir):
        shutil.rmtree(out_dir)
    os.makedirs (out_dir)

    random.seed()

    ghost_dir = op.join(in_dir, '*' + params['ext'])
    ghostpaths = glob.glob (ghost_dir)
    random.shuffle(ghostpaths)
    logging.info ('found ' + str(len(ghostpaths)) + ' in in_dir')
    if not ghostpaths:
        raise Exception ('no image found in: ' + ghost_dir)
    num_per_image = int(params['number'] / len(ghostpaths)) + 1

    counter = 0
    for ghostpath in ghostpaths:
        for patch in __getPatchesFromImage__(ghostpath, num_per_image, params):
            filename = "%08d" % counter + IMAGE_EXT
            filepath = op.join(out_dir, filename)
            cv2.imwrite (filepath, patch)
            counter += 1
            if counter >= params['number']: return

    if counter < params['number']:
        logging.error ('got only ' + str(counter) + ' patches')
    



