#
# This script collects negative training samples from images
# It uses clusters.json file for information about filters
#
# Assumptions are: 1) all cars are labelled in each image (maybe several times)
#

import math
import numpy as np
import scipy.ndimage.filters
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
import setupHelper
import dbInterface  # to check for table
import h5py  # for collectRandomPatchesFromVideoHDF5 (will be removed)

IMAGE_EXT = '.png'


def __generateNoiseMask__ ((height, width, depth), level, avg_pixelation):
    pixelation = avg_pixelation * max(1 + np.random.randn(1)[0] * 0.2, 0.5)
    width_sm  = width / pixelation
    height_sm = height / pixelation
    noise = np.empty((width_sm, height_sm, depth), np.uint8)
    # TODO: change cv2.randn to numpy.random.randn
    cv2.randn (noise, (128,128,128), (level,level,level))
    noise = cv2.resize(noise, (width, height), fx=0, fy=0, interpolation=cv2.INTER_NEAREST)
    return noise


def __grayCircle__ (cursor, (imagefile, ghostfile), out_dir, params):

    params = setupHelper.setParamUnlessThere (params, 'spot_scale', 0.6)

    ghostpath = op.join (os.getenv('CITY_DATA_PATH'), ghostfile)
    if not op.exists (ghostpath):
        raise Exception ('ghost does not exist: ' + ghostpath)
    ghost = cv2.imread(ghostpath)

    # create an empty mask
    mask = np.zeros(ghost.shape, dtype=np.uint8)
    
    car_entries = queryCars (cursor, {'constraint': 'WHERE imagefile = "' + imagefile + '"'})
    logging.debug (str(len(car_entries)) + ' objects found in ' + imagefile)

    for car_entry in car_entries:
        bbox = queryField(car_entry, 'bbox')
        spot_scale = params['spot_scale']
        axes = (int(bbox[2] * spot_scale / 2), int(bbox[3] * spot_scale / 2))
        (cy, cx) = getCenter(bbox2roi(bbox))
        cv2.ellipse (mask, (cx, cy), axes, 0, 0, 360, (255,255,255), -1)

    # blur the mask a little
    mask = scipy.ndimage.filters.gaussian_filter (mask, params['blur_sigma'])

    if params['debug_show']:
        cv2.imshow('debug mask', mask)
        cv2.waitKey()

    # add pixelated color noise
    noise = __generateNoiseMask__ (ghost.shape, params['noise_level'], params['pixelation'])
    noise = noise.astype(float)

    mask = mask.astype(np.float) / 255.0
    ghost = np.multiply(ghost, 1 - mask) + np.multiply(noise, mask)

    cv2.imwrite (op.join(out_dir, op.basename(ghostfile)), ghost)



def __grayMasked__ (cursor, (imagefile, ghostfile), out_dir, params):

    params = setupHelper.setParamUnlessThere (params, 'dilate', 1. / 4)
    params = setupHelper.setParamUnlessThere (params, 'erode', 1. / 2.5)
    params = setupHelper.setParamUnlessThere (params, 'width_step', 0.5)

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()

    logging.info ('start with image: ' + op.basename(imagefile))

    if 'width' not in params.keys() or 'sizemap_path' not in params.keys():
        raise Exception ('no width or sizemap_path in params')

    ghostpath = op.join (CITY_DATA_PATH, ghostfile)
    if not op.exists (ghostpath):
        raise Exception ('ghost does not exist: ' + ghostpath)
    ghost = cv2.imread(ghostpath)

    params['imagefile'] = imagefile
    car_entries = queryCars (cursor, params)
    logging.debug (str(len(car_entries)) + ' objects found in ' + imagefile)

    cursor.execute ('SELECT maskfile FROM images WHERE imagefile = ?', (imagefile,))
    (maskfile,) = cursor.fetchone()
    maskpath = op.join (CITY_DATA_PATH, maskfile)
    if not op.exists(maskpath):
        raise Exception ('maskpath does not exist: ' + maskpath)
    logging.debug ('maskpath: ' + maskpath)
    mask = cv2.imread(maskpath).astype(np.uint8)

    if 'sizemap_path' in params.keys():
        sizemap_path = op.join(CITY_DATA_PATH, params['sizemap_path'])
        if not op.exists(sizemap_path):
            raise Exception ('sizemap_path does not exist: ' + sizemap_path)
        sizemap = cv2.imread(sizemap_path)
        se_sizemap = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (40, 40))
        sizemap = cv2.dilate (sizemap, se_sizemap)
        mask_combined = np.zeros(mask.shape)
        for i in range (2, int(math.log(np.amax(sizemap)) / params['width_step'])):
            width1 = math.exp (params['width_step'] * i)
            width2 = math.exp (params['width_step'] * (i+1))
            logging.debug ('width1, width2: ' + str([width1, width2]))
            width = (width1 + width2) / 2
            sz_dilate = int(width * params['dilate'])
            sz_erode  = int(width * params['erode'])
            logging.debug ('dilate, erode size: ' + str((sz_dilate, sz_erode)))
            mask4size = mask.copy()
            if sz_dilate > 0:
                se_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (sz_dilate, sz_dilate))
                mask4size = cv2.dilate (mask4size, se_dilate)
            if sz_erode > 0:
                se_erode  = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (sz_erode, sz_erode))
                mask4size = cv2.erode  (mask4size, se_erode)
            roi4size = np.logical_and(width1 <= sizemap, sizemap < width2)
            mask_combined[roi4size] = mask4size[roi4size]
            #cv2.imshow('roi4size', roi4size.astype(np.uint8) * 255)
            #cv2.imshow('mask4size', mask4size)
            #cv2.imshow('mask_combined', mask_combined)
            #cv2.waitKey()
        mask = mask_combined
    else:
        sz_dilate = int(params['width'] * params['dilate'])
        sz_erode  = int(params['width'] * params['erode'])
        logging.debug ('dilate size: ' + str(sz_dilate))
        logging.debug ('erode size: ' + str(sz_erode))
        se_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (sz_dilate, sz_dilate))
        se_erode  = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (sz_erode, sz_erode))
        mask = cv2.dilate (mask, se_dilate)
        mask = cv2.erode  (mask, se_erode)

    # blur the mask a little
    mask = scipy.ndimage.filters.gaussian_filter (mask, params['blur_sigma'])

    if params['debug_show']:
        cv2.imshow('debug mask', mask)
        cv2.waitKey()

    # add pixelated color noise
    noise = __generateNoiseMask__ (ghost.shape, params['noise_level'], params['pixelation'])
    noise = noise.astype(float)

    mask = mask.astype(np.float) / 255.0
    ghost = np.multiply(ghost, 1 - mask) + np.multiply(noise, mask)

    cv2.imwrite (op.join(out_dir, op.basename(ghostfile)), ghost)



def negativeGrayspots (db_in_path, db_out_path, out_ghosts_dir, params = {}):
    '''
    Add some gray to the foreground of the source images.
    Save resulting images in 'out_ghosts_dir'. Also save the new .db with new images
    '''
    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    db_in_path  = op.join(CITY_DATA_PATH, db_in_path)
    db_out_path = op.join(CITY_DATA_PATH, db_out_path)
    out_ghosts_dir     = op.join(CITY_DATA_PATH, out_ghosts_dir)

    if not op.exists (out_ghosts_dir):
        os.makedirs (out_ghosts_dir)

    setupHelper.setupCopyDb (db_in_path, db_out_path)

    params = setupHelper.setParamUnlessThere (params, 'method', 'mask')
    params = setupHelper.setParamUnlessThere (params, 'debug_show', False)
    params = setupHelper.setParamUnlessThere (params, 'width', 24)
    params = setupHelper.setParamUnlessThere (params, 'noise_level', 30)
    params = setupHelper.setParamUnlessThere (params, 'pixelation', 10)
    params = setupHelper.setParamUnlessThere (params, 'blur_sigma', 2)

    logging.info ('=== negatives.negativeGrayspots ===')
    logging.info ('db_in_path: ' + db_in_path)
    logging.info ('db_out_path: ' + db_out_path)
    logging.info ('out_ghosts_dir: ' + out_ghosts_dir)
    logging.info ('params:  ' + str(params))

    conn = sqlite3.connect (db_out_path)
    cursor = conn.cursor()

    cursor.execute('SELECT imagefile, ghostfile FROM images')
    image_entries = cursor.fetchall()

    for (imagefile, ghostfile) in image_entries:
        if params['method'] == 'circle':
            __grayCircle__ (cursor, (imagefile, ghostfile), out_ghosts_dir, params)
        elif params['method'] == 'mask':
            __grayMasked__ (cursor, (imagefile, ghostfile), out_ghosts_dir, params)
        else:
            raise Exception ('can not recognize method: ' + params['method'])

        # change the ghostfile entry in the db
        new_ghostfile = op.relpath(op.join(out_ghosts_dir, op.basename(ghostfile)), CITY_DATA_PATH)
        cursor.execute('UPDATE images SET ghostfile=? WHERE imagefile=?', (new_ghostfile, imagefile))

    # remove all cars, matches, and polygons if any
    cursor.execute('DELETE FROM cars')
    if dbInterface.checkTableExists(cursor, 'matches'): 
        cursor.execute('DROP TABLE matches')
    if dbInterface.checkTableExists(cursor, 'polygons'): 
        cursor.execute('DROP TABLE polygons')

    conn.commit()
    conn.close()



def __getPatchesFromImage__ (img, num, params):
    '''
    Collect 'num' of random patches from 'img'.
    '''

    assert (img is not None)
    (im_height, im_width, depth) = img.shape
    logging.debug ('image shape: %dx%d', im_height, im_width)

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

    logging.info ('got ' + str(len(patches)) + ' patches')
    return patches



def __getPatchesFromImagefile__ (imagepath, num, params):
    '''
    Helper wrapper function. Read the image and call __getPatchesFromImage__
    '''

    if not op.exists (imagepath):
        raise Exception ('imagepath does not exist: ' + imagepath)

    img = cv2.imread(imagepath).astype(np.uint8)

    logging.debug (op.basename(imagepath))
    return __getPatchesFromImage__ (img, num, params)



# looks like it's never used since commit #6f8249eb0738b6a633f0988932dee19f13476940
#
def negativePatchesViaMaskfiles (db_path, filters_path, out_dir, params = {}):

    logging.info ('=== negatives.negativePatchesViaMaskfiles ===')
    logging.info ('db_path: ' + db_path)
    logging.info ('filters_path: ' + filters_path)
    logging.info ('out_dir: ' + out_dir)
    logging.info ('params: ' + str(params))

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    db_path      = op.join(CITY_DATA_PATH, db_path)
    filters_path = op.join(CITY_DATA_PATH, filters_path)
    out_dir      = op.join(CITY_DATA_PATH, out_dir)

    params = setupHelper.setParamUnlessThere (params, 'method', 'mask')
    params = setupHelper.setParamUnlessThere (params, 'number', 100)
    params = setupHelper.setParamUnlessThere (params, 'ratio', 0.75)
    params = setupHelper.setParamUnlessThere (params, 'minwidth', 20)
    params = setupHelper.setParamUnlessThere (params, 'maxwidth', 200)
    params = setupHelper.setParamUnlessThere (params, 'max_masked_perc', 0.5)
    params = setupHelper.setParamUnlessThere (params, 'debug_mask', False)

    # check output dir
    if op.exists (out_dir):
        shutil.rmtree(out_dir)
    os.makedirs (out_dir)

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

        for patch in __getPatchesFromImagefile__(ghostpath, num_per_image, params):
            filename = "%08d" % counter + IMAGE_EXT
            filepath = op.join(out_dir, filename)
            cv2.imwrite (filepath, patch)
            counter += 1
            if counter >= params['number']: return

    if counter < params['number']:
        logging.error ('got only ' + str(counter) + ' patches')



# to be replaced by negatives.fillNegativeDbWithBboxes() + exporting.collectGhosts()
#
def negativeImages2patches (in_dir, out_dir, params = {}):

    logging.info ('=== negativeImages2patches ===')
    logging.info ('in_dir: ' + in_dir)
    logging.info ('out_dir: ' + out_dir)
    logging.info ('params: ' + str(params))

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    in_dir       = op.join(CITY_DATA_PATH, in_dir)
    out_dir      = op.join(CITY_DATA_PATH, out_dir)

    params = setupHelper.setParamUnlessThere (params, 'number', 100)
    params = setupHelper.setParamUnlessThere (params, 'ratio', 0.75)
    params = setupHelper.setParamUnlessThere (params, 'minwidth', 20)
    params = setupHelper.setParamUnlessThere (params, 'maxwidth', 200)
    params = setupHelper.setParamUnlessThere (params, 'max_masked_perc', 0.5)
    params = setupHelper.setParamUnlessThere (params, 'ext', '.jpg')
    params = setupHelper.setParamUnlessThere (params, 'debug_mask', False)

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
        for patch in __getPatchesFromImagefile__(ghostpath, num_per_image, params):
            filename = "%08d" % counter + IMAGE_EXT
            filepath = op.join(out_dir, filename)
            cv2.imwrite (filepath, patch)
            counter += 1
            if counter >= params['number']: return

    if counter < params['number']:
        logging.error ('got only ' + str(counter) + ' patches')



def __getBboxesFromImage__ (img, num, params):
    '''
    Collect 'num' of random bboxes from 'img'.
    '''

    assert (img is not None)
    (im_height, im_width, depth) = img.shape
    logging.debug ('image shape: %dx%d', im_height, im_width)

    if 'mask' not in params.keys():
        params['mask'] = np.zeros(img.shape, dtype = np.uint8)

    bboxes = []
    counter = 0
    for i in range (num * 100):

        # randomly select x1, y1, width; calculate height; and extract the patch
        patch_width = random.randint (params['minwidth'], params['maxwidth'])
        patch_height = int(patch_width * params['ratio'])
        if im_width < patch_width or im_height < patch_height:
            continue
        x1 = random.randint (0, im_width - patch_width)
        y1 = random.randint (0, im_height - patch_height)

        # check if patch is within the mask
        masked = params['mask'][y1:y1+patch_height, x1:x1+patch_width, :]
        masked_perc = float(np.count_nonzero(masked)) / masked.size
        if masked_perc > params['max_masked_perc']:
            logging.debug ('masked_perc ' + '%.2f' % masked_perc + ' above limit')
            continue

        bbox = (x1, y1, patch_width, patch_height)
        bboxes.append(bbox)

        if counter >= num: break
        counter += 1

    logging.info ('got ' + str(len(bboxes)) + ' patches')
    return bboxes



def __getBboxesFromImagefile__ (imagepath, num, params):
    '''
    Helper wrapper function. Read the image and call __getBboxesFromImage__
    '''

    if not op.exists (imagepath):
        raise Exception ('imagepath does not exist: ' + imagepath)

    img = cv2.imread(imagepath).astype(np.uint8)

    logging.debug (op.basename(imagepath))
    return __getBboxesFromImage__ (img, num, params)



def fillNegativeDbWithBboxes (db_in_path, db_out_path, params = {}):
    '''
    Populate negative db with negative bboxes.
    The negative db contains ghostfiles which are ready negatives frames.
      Bboxes are extracted from there.
    '''
    logging.info ('=== negatives.fillNegativeDbWithBboxes ===')
    logging.info ('db_in_path: ' + db_in_path)
    logging.info ('db_out_path: ' + db_out_path)
    logging.info ('params: ' + str(params))

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    db_in_path  = op.join(CITY_DATA_PATH, db_in_path)
    db_out_path = op.join(CITY_DATA_PATH, db_out_path)
    setupHelper.setupCopyDb (db_in_path, db_out_path)

    params = setupHelper.setParamUnlessThere (params, 'number', 100)
    params = setupHelper.setParamUnlessThere (params, 'ratio', 0.75)
    params = setupHelper.setParamUnlessThere (params, 'minwidth', 20)
    params = setupHelper.setParamUnlessThere (params, 'maxwidth', 200)
    params = setupHelper.setParamUnlessThere (params, 'max_masked_perc', 0.5)
    params = setupHelper.setParamUnlessThere (params, 'ext', '.jpg')
    params = setupHelper.setParamUnlessThere (params, 'debug_mask', False)

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

    random.seed()

    conn = sqlite3.connect (db_out_path)
    cursor = conn.cursor()

    # get all ghostfiles
    cursor.execute('SELECT imagefile, ghostfile FROM images')
    image_entries = cursor.fetchall()
    num_per_image = int(params['number'] / len(image_entries)) + 1

    # find some good negative bboxes in each ghostfile. Insert them into the output db
    counter = 0
    for (imagefile,ghostfile) in image_entries:
        ghostpath = op.join(CITY_DATA_PATH, ghostfile)
        for bbox in __getBboxesFromImagefile__(ghostpath, num_per_image, params):
            logging.debug ('fillNegativeDbWithBboxes: writing bbox')
            s = 'cars(imagefile,name,x1,y1,width,height)'
            entry = (imagefile, 'negative', bbox[0], bbox[1], bbox[2], bbox[3])
            cursor.execute('INSERT INTO %s VALUES (?,?,?,?,?,?)' % s, entry)
            counter += 1
            if counter >= params['number']: break
        if counter >= params['number']: break

    if counter < params['number']:
        logging.error ('got only ' + str(counter) + ' patches')

    conn.commit()
    conn.close()
    


def collectRandomPatchesFromVideo (video_in_path, out_dir, params = {}):
    '''
    Extract patches from every frame in a video
    Used for unsupervised learning of features in DNN (pre-training)
    Background should already be subtracted
    '''
    setupHelper.setupLogHeader (video_in_path, '', params, 'collectRandomPatchesFromVideo')

    video_in_path = op.join (os.getenv('CITY_DATA_PATH'), video_in_path)
    out_dir       = op.join (os.getenv('CITY_DATA_PATH'), out_dir)

    params = setupHelper.setParamUnlessThere (params, 'number', 100)
    params = setupHelper.setParamUnlessThere (params, 'ratio', 0.75)
    params = setupHelper.setParamUnlessThere (params, 'minwidth', 20)
    params = setupHelper.setParamUnlessThere (params, 'maxwidth', 200)
    params = setupHelper.setParamUnlessThere (params, 'max_masked_perc', 0.5) # not used

    if not op.exists (video_in_path):
        raise Exception ('video does not exist: ' + video_in_path)

    # check output dir
    if op.exists (out_dir):
        shutil.rmtree(out_dir)
    os.makedirs (out_dir)

    random.seed()

    # count the number of frames in the video
    video = cv2.VideoCapture(video_in_path)
    counter_images = 0
    while (True):
        ret, frame = video.read()
        if not ret: break
        counter_images += 1

    logging.info ('video has %d frames', counter_images)
    num_per_image = int(params['number'] / counter_images) + 1

    video = cv2.VideoCapture(video_in_path)
    counter = 0
    while (True):
        ret, frame = video.read()
        if not ret: break

        for patch in __getPatchesFromImage__ (frame, num_per_image, params):
            filename = "%08d" % counter + IMAGE_EXT
            filepath = op.join(out_dir, filename)
            cv2.imwrite (filepath, patch)
            counter += 1
            if counter >= params['number']: return

    if counter < params['number']:
        logging.error ('got only ' + str(counter) + ' patches')



# TODO: after moving datasets to HDF5, make a db+h5 from video,
#       and throw away thos function
#
def collectRandomPatchesFromVideoHDF5 (video_in_path, h5_out_path, params = {}):
    '''
    Extract patches from every frame in a video, and save them as HDF5 file
    Used for unsupervised learning of features in DNN (pre-training)
    Background should already be subtracted
    '''
    setupHelper.setupLogHeader (video_in_path, '', params, 'collectRandomPatchesFromVideo')

    video_in_path = op.join (os.getenv('CITY_DATA_PATH'), video_in_path)
    h5_out_path   = op.join (os.getenv('CITY_DATA_PATH'), h5_out_path)

    params = setupHelper.setParamUnlessThere (params, 'number', 100)
    params = setupHelper.setParamUnlessThere (params, 'ratio', 0.75)
    params = setupHelper.setParamUnlessThere (params, 'minwidth', 20)
    params = setupHelper.setParamUnlessThere (params, 'maxwidth', 200)
    params = setupHelper.setParamUnlessThere (params, 'max_masked_perc', 0.5) # not used
    params = setupHelper.setParamUnlessThere (params, 'write_samples', 0)
    params = setupHelper.setParamUnlessThere (params, 'normalize', True)
    setupHelper.assertParamIsThere (params, 'resize')
    assert (type(params['resize']) == list and len(params['resize']) == 2)

    if not op.exists (video_in_path):
        raise Exception ('video does not exist: ' + video_in_path)

    random.seed()

    # make data numpy array first, and write all to there
    # TODO: create dataset first and write directly to there, without a huge array in memory
    (width, height) = tuple(params['resize'])
    data = np.zeros((params['number'], 3, height, width), dtype='float32')

    # count the number of frames in the video
    video = cv2.VideoCapture(video_in_path)
    counter_images = 0
    while (True):
        ret, frame = video.read()
        if not ret: break
        counter_images += 1

    logging.info ('video has %d frames', counter_images)
    num_per_image = int(params['number'] / counter_images) + 1

    video = cv2.VideoCapture(video_in_path)
    counter = 0
    while (True):
        ret, frame = video.read()
        if not ret: break

        for patch in __getPatchesFromImage__ (frame, num_per_image, params):

            # save a sample patch as an image
            if counter < params['write_samples']:
                patchsuffix = '-%d%s' % (counter, IMAGE_EXT)
                patchpath = op.splitext(h5_out_path)[0] + patchsuffix
                logging.debug ('patchpath: %s' % patchpath)
                cv2.imwrite(patchpath, patch)

            # write to intermediate numpy arrays
            patch = np.transpose(patch.astype('float32'), (2,0,1))  # why not (1,2,0)?
            if params['normalize']: patch /= 255.
            data[counter,:,:,:] = patch

            counter += 1
            if counter >= params['number']: break
        if counter >= params['number']: break

    # process a case where for any reason could not get enough patches
    if counter < params['number']:
        logging.error ('got only ' + str(counter) + ' patches')
        # TODO: not tested
        data.resize((counter, 3, height, width))

    # create the hdf5
    with h5py.File(h5_out_path, 'w') as f:
        f['data'] = data





