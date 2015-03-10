#!/bin/python

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
from dbInterface import deleteCar, queryField, queryCars
from utilities import bbox2roi, image2ghost, getCenter



class NegativesGrayspots:

    def processImage (self, (imagefile, backfile), filter_group, out_dir):

        imagepath = op.join (os.getenv('CITY_DATA_PATH'), imagefile)
        if not op.exists (imagepath):
            raise Exception ('image does not exist: ' + imagepath)
        img = cv2.imread(imagepath)

        # update backpath and backimage
        backpath = op.join (os.getenv('CITY_DATA_PATH'), backfile)
        if not hasattr(self, 'backimage') or self.backpath != backpath:
            logging.debug ('update backimage from ' + backfile)
            self.backpath = backpath
            if not op.exists (backpath):
                raise Exception ('backimage does not exist: ' + backfile)
            self.backimage = cv2.imread(self.backpath).astype(np.int32)

        img = image2ghost (img, self.backimage)

        filter_group['imagefile'] = imagefile
        car_entries = queryCars (self.cursor, filter_group)
        logging.debug (str(len(car_entries)) + ' objects found for "' + 
                       filter_group['filter'] + '" in ' + imagefile)

        for car_entry in car_entries:
            bbox = queryField(car_entry, 'bbox-w-offset')
            axes = (int(bbox[2] * .3), int(bbox[3] * .3))
            (cy, cx) = getCenter(bbox2roi(bbox))
            cv2.ellipse (img, (cx, cy), axes, 0, 0, 360, (128,128,128), -1)

        cv2.imwrite (op.join(out_dir, op.basename(imagefile)), img)




    def processDb (self, db_path, filters_path, out_dir):

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

        self.conn = sqlite3.connect (db_path)
        self.cursor = self.conn.cursor()

        for filter_group in filters_groups:
            assert ('filter' in filter_group)
            logging.info ('filter group ' + filter_group['filter'])

            # create a dir for cluster
            cluster_dir = op.join (out_dir, filter_group['filter'])
            if op.exists (cluster_dir):
                shutil.rmtree (cluster_dir)
            os.makedirs (cluster_dir)

            self.cursor.execute('SELECT imagefile,backimage FROM images')
            image_entries = self.cursor.fetchall()

            for image_entry in image_entries:
                self.processImage (image_entry, filter_group, cluster_dir)

        self.conn.close()


