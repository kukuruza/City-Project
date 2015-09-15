#
# This script collects negative training samples from images
# It uses clusters.json file for information about filters
#
# Assumptions are: 1) all cars are labelled in each image (maybe several times)
#

import os, sys, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/backend'))
import math
import numpy as np
import scipy.ndimage.filters
import cv2
import collections
import logging
import json
import glob
import shutil
import sqlite3
import random
from utilities import bbox2roi, getCenter
import helperSetup
import helperDb
import helperImg


def _generateNoiseMask_ ((height, width, depth), level, avg_pixelation):
    ''' Return gray image with noise, of size (height, width, depth) and type float '''
    if avg_pixelation < 1: avg_pixelation = 1  # everything under 1 is no pixelation
    pixelation = avg_pixelation * max(1 + np.random.randn(1)[0] * 0.2, 0.5)
    width_sm  = width / pixelation
    height_sm = height / pixelation
    noise = np.empty((width_sm, height_sm, depth), np.uint8)
    # TODO: change cv2.randn to numpy.random.randn
    cv2.randn (noise, (128,128,128), (level,level,level))
    noise = cv2.resize(noise, (width, height), fx=0, fy=0, interpolation=cv2.INTER_NEAREST)
    return noise.astype(float)


def _grayCircle_ (c, imagefile, out_images_dir, params):

    helperSetup.assertParamIsThere  (params, 'blur_sigma')
    helperSetup.assertParamIsThere  (params, 'noise_level')
    helperSetup.assertParamIsThere  (params, 'pixelation')
    helperSetup.setParamUnlessThere (params, 'spot_scale',   0.6)
    helperSetup.setParamUnlessThere (params, 'debug_show',   False)
    helperSetup.setParamUnlessThere (params, 'image_processor', helperImg.ProcessorImagefile())

    image = params['image_processor'].imread(imagefile)

    # create an empty mask
    mask = np.zeros(image.shape, dtype=np.uint8)

    c.execute ('SELECT * FROM cars WHERE imagefile = ?', (imagefile,))
    car_entries = c.fetchall()
    logging.debug ('%d objects found in %s' % (len(car_entries), imagefile))

    for car_entry in car_entries:
        bbox = helperDb.carField(car_entry, 'bbox')
        spot_scale = params['spot_scale']
        axes = (int(bbox[2] * spot_scale / 2), int(bbox[3] * spot_scale / 2))
        (cx, cy) = getCenter(bbox2roi(bbox))
        cv2.ellipse (mask, (cx, cy), axes, 0, 0, 360, (255,255,255), -1)

    # blur the mask a little
    mask = scipy.ndimage.filters.gaussian_filter (mask, params['blur_sigma'])

    if params['debug_show']:
        cv2.imshow('debug mask', mask)
        cv2.waitKey()

    # add pixelated color noise
    noise = _generateNoiseMask_ (image.shape, params['noise_level'], params['pixelation'])

    mask = mask.astype(np.float) / 255.0
    image = np.multiply(image, 1 - mask) + np.multiply(noise, mask)

    params['image_processor'].imwrite (image, op.join(out_images_dir, op.basename(imagefile)))



def _grayMasked_ (c, imagefile, out_images_dir, params):

    helperSetup.assertParamIsThere  (params, 'blur_sigma')
    helperSetup.assertParamIsThere  (params, 'noise_level')
    helperSetup.assertParamIsThere  (params, 'pixelation')
    helperSetup.setParamUnlessThere (params, 'dilate',       1. / 4)
    helperSetup.setParamUnlessThere (params, 'erode',        1. / 2.5)
    helperSetup.setParamUnlessThere (params, 'width_step',   0.5)
    helperSetup.setParamUnlessThere (params, 'debug_show',   False)
    helperSetup.setParamUnlessThere (params, 'relpath',      os.getenv('CITY_DATA_PATH'))
    helperSetup.setParamUnlessThere (params, 'image_processor', helperImg.ProcessorImagefile())

    image = params['image_processor'].imread(imagefile)

    c.execute ('SELECT * FROM cars WHERE imagefile = ?', (imagefile,))
    car_entries = c.fetchall()
    logging.debug ('%d objects found in %s' % (len(car_entries), imagefile))

    c.execute ('SELECT maskfile FROM images WHERE imagefile = ?', (imagefile,))
    (maskfile,) = c.fetchone()
    mask = params['image_processor'].maskread(maskfile)

    if 'size_map_path' in params:
        params['size_map_path'] = op.join(params['relpath'], params['size_map_path'])
        size_map = cv2.imread(params['size_map_path'], 0)
        if size_map is None:
            raise Exception ('grayMasked: failed to read size_map from: %s' % params['size_map_path'])
        if size_map.shape != mask.shape:
            raise Exception ('grayMasked: size_map and mask shapes do not match (%s vs %s)' % 
                             (params['size_map_path'], maskfile))
        se_size_map = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (40, 40))
        size_map = cv2.dilate (size_map, se_size_map)
        mask_combined = np.zeros(mask.shape)
        for i in range (2, int(math.log(np.amax(size_map)) / params['width_step'])):
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
            roi4size = np.logical_and(width1 <= size_map, size_map < width2)
            mask_combined[roi4size] = mask4size[roi4size]
            #cv2.imshow('roi4size', roi4size.astype(np.uint8) * 255)
            #cv2.imshow('mask4size', mask4size)
            #cv2.imshow('mask_combined', mask_combined)
            #cv2.waitKey()
        mask = mask_combined
    elif 'width' in params:
        sz_dilate = int(params['width'] * params['dilate'])
        sz_erode  = int(params['width'] * params['erode'])
        logging.debug ('dilate size: ' + str(sz_dilate))
        logging.debug ('erode size: ' + str(sz_erode))
        se_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (sz_dilate, sz_dilate))
        se_erode  = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (sz_erode, sz_erode))
        mask = cv2.dilate (mask, se_dilate)
        mask = cv2.erode  (mask, se_erode)
    else:
        raise Exception ('no "width" and no "sizemap_path" in params')

    # blur the mask a little
    mask = scipy.ndimage.filters.gaussian_filter (mask, params['blur_sigma'])

    if params['debug_show']:
        cv2.imshow('debug mask', mask)
        cv2.waitKey()

    # add pixelated color noise
    noise = _generateNoiseMask_ (image.shape, params['noise_level'], params['pixelation'])

    mask = np.asarray(np.dstack((mask, mask, mask)))
    mask = mask.astype(np.float) / 255.0
    image = np.multiply(image, 1 - mask) + np.multiply(noise, mask)

    params['image_processor'].imwrite (image, op.join(out_images_dir, op.basename(imagefile)))



def negativeGrayspots (c, out_images_dir, params = {}):
    '''
    Add some gray to the foreground of the source images.
    Save resulting images in 'out_images_dir'. Also save the new .db with new images
    '''
    logging.info ('=== negatives.negativeGrayspots ===')
    logging.info ('out_images_dir: %s' % out_images_dir)
    helperSetup.setParamUnlessThere (params, 'method',      'mask')
    helperSetup.setParamUnlessThere (params, 'debug_show',  False)
    helperSetup.setParamUnlessThere (params, 'noise_level', 30)
    helperSetup.setParamUnlessThere (params, 'pixelation',  10)
    helperSetup.setParamUnlessThere (params, 'blur_sigma',  2)
    helperSetup.setParamUnlessThere (params, 'relpath',     os.getenv('CITY_DATA_PATH'))

    out_images_dir = op.join(params['relpath'], out_images_dir)
    if not op.exists (out_images_dir):
        os.makedirs (out_images_dir)

    c.execute('SELECT imagefile FROM images')
    image_entries = c.fetchall()

    for (imagefile,) in image_entries:
        if params['method'] == 'circle':
            _grayCircle_ (c, imagefile, out_images_dir, params)
        elif params['method'] == 'mask':
            _grayMasked_ (c, imagefile, out_images_dir, params)
        else:
            raise Exception ('can not recognize method: %s' % params['method'])

        # change the imagefile entry in the db
        new_imagefile = op.relpath(op.join(out_images_dir, op.basename(imagefile)), params['relpath'])
        c.execute('UPDATE images SET imagefile=? WHERE imagefile=?', (new_imagefile, imagefile))

    c.execute('DELETE FROM cars')
    c.execute('DELETE FROM matches')



def _getBboxesFromImage_ (image, num, params):
    '''
    Collect 'num' of random bboxes from 'img'.
    '''
    helperSetup.setParamUnlessThere (params, 'minwidth', 20)
    helperSetup.setParamUnlessThere (params, 'maxwidth', 200)
    helperSetup.setParamUnlessThere (params, 'ratio',    0.75)
    helperSetup.setParamUnlessThere (params, 'max_masked_perc', 0.5)
    helperSetup.setParamUnlessThere (params, 'mask', np.zeros(image.shape[0:2], dtype = np.uint8))

    assert (image is not None)
    (im_height, im_width, depth) = image.shape
    logging.debug ('image shape: %dx%d', im_height, im_width)
    assert (params['mask'].shape == (im_height, im_width))

    bboxes = []
    counter = 0
    for i in range (num * 100):  # 100x more than necessary, in case many are filtered out

        # randomly select x1, y1, width; calculate height; and extract the patch
        patch_width = random.randint (params['minwidth'], params['maxwidth'])
        patch_height = int(patch_width * params['ratio'])
        if im_width < patch_width or im_height < patch_height:
            continue
        x1 = random.randint (0, im_width - patch_width)
        y1 = random.randint (0, im_height - patch_height)

        # check if patch is within the mask
        masked = params['mask'][y1:y1+patch_height, x1:x1+patch_width]
        masked_perc = float(np.count_nonzero(masked)) / masked.size
        if masked_perc > params['max_masked_perc']:
            logging.debug ('masked_perc %.2f above limit' % masked_perc)
            continue

        bbox = (x1, y1, patch_width, patch_height)
        bboxes.append(bbox)

        counter += 1
        if counter >= num: break

    logging.info ('got %d bboxes' % len(bboxes))
    return bboxes



def fillNegativeDbWithBboxes (c, params = {}):
    '''
    Populate negative db with negative bboxes.
    The negative db contains imagefiles which are ready negatives frames.
      Bboxes are extracted from there.
    '''
    logging.info ('=== negatives.fillNegativeDbWithBboxes ===')
    helperSetup.setParamUnlessThere (params, 'number', 100)
    helperSetup.setParamUnlessThere (params, 'debug_mask', False)
    helperSetup.setParamUnlessThere (params, 'relpath',      os.getenv('CITY_DATA_PATH'))
    helperSetup.setParamUnlessThere (params, 'image_processor', helperImg.ProcessorImagefile())

    # if 'size_map_path' provided, load it to further use as a mask
    if 'size_map_path' in params:
        params['size_map_path'] = op.join(params['relpath'], params['size_map_path'])
        if not op.exists(params['size_map_path']):
            raise Exception ('size_map_path does not exist: ' + params['size_map_path'])
        size_map_path  = op.join(os.getenv('CITY_DATA_PATH'), params['size_map_path'])
        size_map  = cv2.imread (params['size_map_path'], 0).astype(np.float32)
        logging.info ('will load size_map from: ' + size_map_path)
        assert size_map is not None
        params['mask'] = (size_map == 0)
        if params['debug_mask']:
            cv2.imshow('size_map mask', params['mask'])
            cv2.waitKey()

    c.execute('DELETE FROM cars')
    c.execute('DELETE FROM matches')

    random.seed()

    # get all imagefiles
    c.execute('SELECT imagefile FROM images')
    image_entries = c.fetchall()
    num_per_image = int(params['number'] / len(image_entries)) + 1

    # find some good negative bboxes in each imagefile. Insert them into the output db
    counter = 0
    for (imagefile,) in image_entries:
        image = params['image_processor'].imread(imagefile)
        for bbox in _getBboxesFromImage_(image, num_per_image, params):
            logging.debug ('fillNegativeDbWithBboxes: writing bbox')
            s = 'cars(imagefile,name,x1,y1,width,height)'
            entry = (imagefile, 'negative', bbox[0], bbox[1], bbox[2], bbox[3])
            c.execute('INSERT INTO %s VALUES (?,?,?,?,?,?)' % s, entry)
            counter += 1
            if counter >= params['number']: break
        if counter >= params['number']: break

    if counter < params['number']:
        logging.error ('fillNegativeDbWithBboxes: got only %d patches' % counter)
