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
import os.path as op
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


    def collectGhosts (self, db_path, filters_path, out_dir, params = {}):
        '''Cluster cars and save the patches by cluster

           Find cars in paths specified in data_list_path,
           use filters to cluster and transform,
           and save the ghosts '''

        logging.info ('=== clustering.collectGhosts ===')
        logging.info ('db_path: ' + db_path)
        logging.info ('filters_path: ' + filters_path)
        logging.info ('out_dir: ' + out_dir)
        logging.info ('params: ' + str(params))
        logging.info ('')

        # open db
        if not op.exists (db_path):
            raise Exception ('db does not exist: ' + db_path)
        conn = sqlite3.connect (db_path)
        cursor = conn.cursor()

        # load clusters
        if not op.exists(filters_path):
            raise Exception('filters_path does not exist: ' + filters_path)
        filters_file = open(filters_path)
        filters_groups = json.load(filters_file)
        filters_file.close()

        # delete 'out_dir' dir, and recreate it
        logging.warning ('will delete existing out dir: ' + out_dir)
        if op.exists (out_dir):
            shutil.rmtree (out_dir)
        os.makedirs (out_dir)

        for filter_group in filters_groups:
            assert ('filter' in filter_group)
            logging.info ('filter group ' + filter_group['filter'])

            cluster_dir = op.join (out_dir, filter_group['filter'])
            os.makedirs (cluster_dir)

            # get db entries
            car_entries = queryCars (cursor, filter_group)

            # write ghosts for each entry
            for car_entry in car_entries:

                # update imagefile and image
                imagefile = queryField (car_entry, 'imagefile')
                cursor.execute('SELECT ghostfile FROM images WHERE imagefile=?', (imagefile,))
                (ghostfile,) = cursor.fetchone()
                ghostpath = op.join (os.getenv('CITY_DATA_PATH'), ghostfile)
                if not hasattr(self, 'imagefile') or self.ghostfile != ghostfile:
                    logging.debug ('update image from ' + ghostfile)
                    self.ghostfile = ghostfile
                    if not op.exists (imagepath):
                        raise Exception ('ghostpath does not exist: ' + ghostpath)
                    self.ghost = cv2.imread(ghostpath)

                carid, patch = self.getGhost (car_entry, self.ghost)

                filename = "%08d" % carid + IMAGE_EXT
                filepath = op.join(cluster_dir, filename)

                if 'resize' in filter_group.keys():
                    assert (type(filter_group['resize']) == list)
                    assert (len(filter_group['resize']) == 2)
                    patch = cv2.resize(patch, tuple(filter_group['resize']))

                cv2.imwrite(filepath, patch)

        conn.close()

        # write info
        with open(op.join(out_dir, 'readme.txt'), 'w') as readme:
            readme.write('from database ' + db_path + '\n')
            readme.write('with filters  ' + filters_path + '\n')



    def writeInfoFile (self, db_path, filters_path, out_dir, params = {}):

        logging.info ('=== clustering.writeInfoFile ===')
        logging.info ('db_path: ' + db_path)
        logging.info ('filters_path: ' + filters_path)
        logging.info ('out_dir: ' + out_dir)
        logging.info ('params: ' + str(params))
        logging.info ('')

        if 'dupl_num' in params.keys(): 
            dupl_num = params['dupl_num']
        else:
            dupl_num = 1

        # open db
        if not op.exists (db_path):
            raise Exception ('db does not exist: ' + db_path)
        conn = sqlite3.connect (db_path)
        cursor = conn.cursor()

        # load clusters
        if not op.exists(filters_path):
            raise Exception('filters_path does not exist: ' + filters_path)
        filters_file = open(filters_path)
        filters_groups = json.load(filters_file)
        filters_file.close()

        # delete 'out_dir' dir, and recreate it
        logging.warning ('will delete existing out dir: ' + out_dir)
        if op.exists (out_dir):
            shutil.rmtree (out_dir)
        os.makedirs (out_dir)

        for filter_group in filters_groups:
            assert ('filter' in filter_group)

            info_file = open(op.join(out_dir, filter_group['filter'] + '.dat'), 'w')

            cursor.execute('SELECT imagefile, ghostfile FROM images')
            imagefiles = cursor.fetchall()

            counter = 0
            for (imagefile, ghostfile) in imagefiles:

                # get db entries
                filter_group['imagefile'] = imagefile
                car_entries = queryCars (cursor, filter_group)
                counter += len(car_entries)

                # skip if there are no objects
                if not car_entries:
                    continue

                ghostpath = op.join (os.getenv('CITY_DATA_PATH'), ghostfile)
                info_file.write (op.relpath(ghostpath, out_dir))
                info_file.write (' ' + str(len(car_entries)))

                for car_entry in car_entries:
                    bbox = queryField(car_entry, 'bbox-w-offset')
                    # write several times, for generation multiple objects
                    for i in range(dupl_num):
                        info_file.write ('   ' + ' '.join(str(e) for e in bbox))

                info_file.write('\n')

            logging.info ('instances of ' + filter_group['filter'] + ': ' + str(counter))

        info_file.close()
        conn.close()

        # write info
        with open(op.join(out_dir, 'readme.txt'), 'w') as readme:
            readme.write('from database ' + db_path + '\n')
            readme.write('with filters  ' + filters_path + '\n')

