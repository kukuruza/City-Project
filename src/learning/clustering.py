#!/usr/bin/python
#
# Clustering aims to prepare Car/PyCar objects collected from different sources
#   into dataset that can be used for training/testing.
#
# The input of the module is collections of cars, the output is folders 
#   with patches that meet specified requirements (e.g. orientation.)
#
# Clustering cars based by orientation/size/type/color is set by user.
# The sources of objects are set in a config files.
# Format of output dataset can be different for different packages.
# Maybe splitting into training/testing can be done here.
#

IMAGE_EXT = '.png'


import logging
import os, sys
import os.path as OP
import shutil
import glob
import json
import sqlite3
import numpy as np, cv2
from dbInterface import queryCars, queryField
from utilities import bbox2roi



class Clusterer:

    def getGhost (self, car_entry, image):
        assert (car_entry is not None)

        carid = queryField (car_entry, 'id')
        bbox = queryField(car_entry, 'bbox-w-offset')
        roi = bbox2roi(bbox)
        (height, width, depth) = image.shape
        if roi[2] > height and roi[3] > width:
            raise Exception ('bad roi for ' + queryField(car_entry, 'imagefile'))

        ghost = image [roi[0]:roi[2]+1, roi[1]:roi[3]+1]
        return (carid, ghost)


    def collectGhosts (self, db_path, filters_path, out_dir):
        '''Cluster cars and save the patches by cluster

           Find cars in paths specified in data_list_path,
           use filters to cluster and transform,
           and save the ghosts '''

        if not OP.exists (db_path):
            raise Exception ('db does not exist: ' + db_path)

        conn = sqlite3.connect (db_path)
        cursor = conn.cursor()

        # load clusters
        if not OP.exists(filters_path):
            raise Exception('filters_path does not exist: ' + filters_path)
        filters_file = open(filters_path)
        filters_groups = json.load(filters_file)
        filters_file.close()

        counter_by_cluster = {}

        for filter_group in filters_groups:
            assert ('filter' in filter_group)
            logging.info ('filter group ' + filter_group['filter'])

            # delete 'cluster_dir' dir, and recreate it
            cluster_dir = OP.join (out_dir, filter_group['filter'])
            if OP.exists (cluster_dir):
                logging.warning ('will delete existing cluster dir: ' + cluster_dir)
                shutil.rmtree (cluster_dir)
            os.makedirs (cluster_dir)

            # get db entries
            car_entries = queryCars (cursor, filter_group)
            counter_by_cluster[filter_group['filter']] = len(car_entries)

            # write ghosts for each entry
            for car_entry in car_entries:

                # update imagefile and image
                imagefile = queryField (car_entry, 'imagefile')
                imagepath = OP.join (os.getenv('CITY_DATA_PATH'), imagefile)
                if not hasattr(self, 'imagefile') or self.imagefile != imagefile:
                    logging.debug ('update image from ' + imagefile)
                    self.imagefile = imagefile
                    if not OP.exists (imagepath):
                        raise Exception ('imagepath does not exist: ' + imagepath)
                    self.image = cv2.imread(imagepath)

                carid, ghost = self.getGhost (car_entry, self.image)

                filename = "%08d" % carid + IMAGE_EXT
                filepath = OP.join(cluster_dir, filename)

                if 'resize' in filter_group.keys():
                    assert (type(filter_group['resize']) == list)
                    assert (len(filter_group['resize']) == 2)
                    ghost = cv2.resize(ghost, tuple(filter_group['resize']))

                cv2.imwrite(filepath, ghost)

        conn.close()

        return counter_by_cluster

