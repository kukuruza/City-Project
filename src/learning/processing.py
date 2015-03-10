#!/bin/python

import numpy as np
import cv2
import os, sys
import collections
import logging
import os.path as op
import glob
import shutil
import sqlite3
from dbInterface import deleteCar, queryField
from utilities import bbox2roi, roi2bbox, bottomCenter


#
# expandRoiFloat expands a ROI, and clips it within borders
#
def expandRoiFloat (roi, (imheight, imwidth), (perc_y, perc_x)):
    half_delta_y = float(roi[2] + 1 - roi[0]) * perc_y / 2
    half_delta_x = float(roi[3] + 1 - roi[1]) * perc_x / 2
    # expand each side
    roi[0] -= half_delta_y
    roi[1] -= half_delta_x
    roi[2] += half_delta_y
    roi[3] += half_delta_x
    # make integer
    roi = [int(x) for x in roi]
    # move to clip into borders
    if roi[0] < 0:
        roi[2] += abs(roi[0])
        roi[0] = 0
    if roi[1] < 0:
        roi[3] += abs(roi[1])
        roi[1] = 0
    if roi[2] > imheight-1:
        roi[0] -= abs((imheight-1) - roi[2])
        roi[2] = imheight-1
    if roi[3] > imwidth-1:
        roi[1] -= abs((imwidth-1) - roi[3])
        roi[3] = imwidth-1
    # check that now averything is within borders (bbox is not too big)
    assert (roi[0] >= 0 and roi[1] >= 0)
    assert (roi[2] <= imheight-1 and roi[3] <= imwidth-1)
    return roi


#
# expands a ROI to keep 'ratio', and maybe more, up to 'expand_perc'
#
def expandRoiToRatio (roi, (imheight, imwidth), expand_perc, ratio):
    # adjust width and height to ratio
    height = float(roi[2] + 1 - roi[0])
    width  = float(roi[3] + 1 - roi[1])
    if height / width < ratio:
       perc = ratio * width / height - 1
       roi = expandRoiFloat (roi, (imheight, imwidth), (perc, 0))
    else:
       perc = height / width / ratio - 1
       roi = expandRoiFloat (roi, (imheight, imwidth), (0, perc))
    # additional expansion
    perc = expand_perc - perc
    if perc > 0:
        roi = expandRoiFloat (roi, (imheight, imwidth), (perc, perc))
    return roi





class Processor:

    border_thresh_perc = 0.03
    expand_perc = 0.1
    target_ratio = 0.75   # height / width
    keep_ratio = False
    size_acceptance = (0.4, 2)
    ratio_acceptance = (0.4, 1.5)
    sizemap_dilate = 21
    debug_show = False

    def __init__(self, params):
        if 'border_thresh_perc' in params.keys(): 
            self.border_thresh_perc = params['border_thresh_perc']
        if 'expand_perc' in params.keys(): 
            self.expand_perc = params['expand_perc']
        if 'target_ratio' in params.keys(): 
            self.target_ratio = params['target_ratio']
        if 'keep_ratio' in params.keys(): 
            self.keep_ratio = params['keep_ratio']
        if 'size_acceptance' in params.keys(): 
            self.size_acceptance = params['size_acceptance']
        if 'ratio_acceptance' in params.keys(): 
            self.ratio_acceptance = params['ratio_acceptance']
        if 'sizemap_dilate' in params.keys(): 
            self.sizemap_dilate = params['sizemap_dilate']
        if 'debug_show' in params.keys():
            self.debug_show = params['debug_show']
        if 'debug_sizemap' in params.keys(): debug_sizemap = params['debug_sizemap']
        else: debug_sizemap = False

        if 'geom_maps_dir' in params.keys():
            self.loadMaps (params['geom_maps_dir'])
        else:
            raise Exception ('BaseProcessor: geom_maps_dir is not given in params')

        if debug_sizemap:
            cv2.imshow ('size_map original', self.size_map)

        # dilate size_map
        kernel = np.ones ((self.sizemap_dilate, self.sizemap_dilate), 'uint8')
        self.size_map = cv2.dilate (self.size_map, kernel)

        if debug_sizemap:
            cv2.imshow ('size_map dilated', self.size_map)
            cv2.waitKey(-1)



    # this function knows all about size- and orientation- maps
    def loadMaps (self, geom_maps_dir):
        size_map_path  = op.join (geom_maps_dir, 'sizeMap.tiff')
        pitch_map_path = op.join (geom_maps_dir, 'pitchMap.tiff')
        yaw_map_path   = op.join (geom_maps_dir, 'yawMap.tiff')
        self.size_map  = cv2.imread (size_map_path, 0).astype(np.float32)
        self.pitch_map = cv2.imread (pitch_map_path, 0).astype(np.float32)
        self.yaw_map   = cv2.imread (yaw_map_path, -1).astype(np.float32)
        self.yaw_map   = cv2.add (self.yaw_map, -360)


    def isPolygonAtBorder (self, xs, ys, width, height):
        border_thresh = (height + width) / 2 * self.border_thresh_perc
        dist_to_border = min (xs, [width - x for x in xs], ys, [height - y for y in ys])
        num_too_close = sum([x < border_thresh for x in dist_to_border])
        return num_too_close >= 2


    def isWrongSize (self, roi):
        bc = bottomCenter(roi)
        # whatever definition of size
        size = ((roi[2] - roi[0]) + (roi[3] - roi[1])) / 2
        return self.size_map [bc[0], bc[1]] * self.size_acceptance[0] > size or \
               self.size_map [bc[0], bc[1]] * self.size_acceptance[1] < size


    def isBadRatio (self, roi):
        ratio = float(roi[2] - roi[0]) / (roi[3] - roi[1])   # height / width
        return ratio < self.ratio_acceptance[0] or ratio > self.ratio_acceptance[1]


    def assignOrientation (self, roi):
        bc = bottomCenter(roi)
        # get corresponding yaw-pitch
        yaw   = self.yaw_map   [bc[0], bc[1]]
        pitch = self.pitch_map [bc[0], bc[1]]
        return (float(yaw), float(pitch))


    def debugShowAddRoi (self, img, roi, (offsety, offsetx), flag):
        if self.debug_show: 
            if flag == 'border':
                color = (0,255,255)
            elif flag == 'badroi':
                color = (0,0,255)
            elif flag == 'good':
                color = (255,0,0)
            else:
                return
            roi[0] += offsety
            roi[1] += offsetx
            roi[2] += offsety
            roi[3] += offsetx
            cv2.rectangle (img, (roi[1], roi[0]), (roi[3], roi[2]), color)



    def processCar (self, car_entry):

        carid = queryField(car_entry, 'id')
        roi = bbox2roi (queryField(car_entry, 'bbox'))
        imagefile = queryField(car_entry, 'imagefile')
        offsetx   = queryField(car_entry, 'offsetx')
        offsety   = queryField(car_entry, 'offsety')

        # prefer to duplicate query rather than pass parameters to function
        self.cursor.execute('SELECT width,height FROM images WHERE imagefile=?', (imagefile,))
        (width,height) = self.cursor.fetchone()

        # get polygon
        self.cursor.execute('SELECT x,y FROM polygons WHERE carid=?', 
                            (queryField(car_entry, 'id'),))
        polygon_entries = self.cursor.fetchall()
        xs = [polygon_entry[0] for polygon_entry in polygon_entries]
        ys = [polygon_entry[1] for polygon_entry in polygon_entries]
        assert (len(xs) > 2 and min(xs) != max(xs) and min(ys) != max(ys))

        # filter bad ones
        is_bad = False
        if self.isPolygonAtBorder(xs, ys, width, height): 
            logging.info ('border polygon ' + str(xs) + ', ' + str(ys))
            flag = 'border'
            is_bad = True
        elif self.isWrongSize(roi):
            logging.info ('wrong size of car in ' + str(roi))
            flag = 'badroi'
            is_bad = True
        elif self.isBadRatio(roi):
            logging.info ('bad ratio of roi ' + str(roi))
            flag = 'badroi'
            is_bad = True

        if is_bad:
            deleteCar (self.cursor, carid)
            self.debugShowAddRoi (self.img_show, roi, (offsety, offsetx), flag)
            return

        # assign orientation
        (yaw, pitch) = self.assignOrientation (roi)

        # expand bbox
        if self.keep_ratio:
            roi = expandRoiToRatio (roi, (height, width), self.expand_perc, self.target_ratio)
        else:
            roi = expandRoiFloat (roi, (height, width), (self.expand_perc, self.expand_perc))
        self.debugShowAddRoi (self.img_show, roi, (offsety, offsetx), 'good')

        self.cursor.execute('''UPDATE cars
                               SET x1=?, y1=?, width=?, height=?, yaw=?, pitch=? 
                               WHERE id=?''', tuple (roi2bbox(roi) + [yaw, pitch] + [carid]))



    def processDb (self, db_in_path, db_out_path):

        if not op.exists (db_in_path):
            raise Exception ('db does not exist: ' + db_in_path)

        if op.exists (db_out_path):
            logging.warning ('will delete existing db_out_path')
            os.remove (db_out_path)

        # copy input database into the output one
        shutil.copyfile(db_in_path, db_out_path)

        self.conn = sqlite3.connect (db_out_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute('SELECT imagefile FROM images')
        image_entries = self.cursor.fetchall()

        for (imagefile,) in image_entries:

            imagepath = op.join (os.getenv('CITY_DATA_PATH'), imagefile)
            if not op.exists (imagepath):
                raise Exception ('image does not exist: ' + imagepath)
            self.img_show = cv2.imread(imagepath) if self.debug_show else None

            self.cursor.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
            car_entries = self.cursor.fetchall()
            logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

            for car_entry in car_entries:
                self.processCar (car_entry)

            if self.debug_show: 
                cv2.imshow('debug_show', self.img_show)
                cv2.waitKey(-1)

        self.conn.commit()
        self.conn.close()

