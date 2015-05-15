#!/usr/bin/python
#
# Clustering aims to prepare patches collected from different sources
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
import setupHelper



def collectGhosts (db_in_path, out_dir, params = {}):
    '''
    Save car ghosts into out_dir
    '''

    db_in_path = op.join (os.getenv('CITY_DATA_PATH'), db_in_path)
    out_dir    = op.join (os.getenv('CITY_DATA_PATH'), out_dir)

    setupHelper.setupLogHeader (db_in_path, '', params, 'collectGhosts')

    # open db
    if not op.exists (db_in_path):
        raise Exception ('db does not exist: ' + db_in_path)
    conn = sqlite3.connect (db_in_path)
    cursor = conn.cursor()

    # delete 'out_dir' dir, and recreate it
    if op.exists (out_dir):
        logging.warning ('will delete existing out dir: ' + out_dir)
        shutil.rmtree (out_dir)
    os.makedirs (out_dir)

    # get db entries

    car_entries = queryCars (cursor, params)
    logging.info ('found images: ' + str(len(car_entries)))

    ghostfile0 = None

    # write ghosts for each entry
    for car_entry in car_entries:

        # update imagefile and image
        imagefile = queryField (car_entry, 'imagefile')
        cursor.execute('SELECT ghostfile FROM images WHERE imagefile=?', (imagefile,))
        (ghostfile,) = cursor.fetchone()
        ghostpath = op.join (os.getenv('CITY_DATA_PATH'), ghostfile)
        if ghostfile0 is None or ghostfile0 != ghostfile:
            logging.debug ('update image from ' + ghostfile)
            ghostfile0 = ghostfile
            if not op.exists (ghostpath):
                raise Exception ('ghostpath does not exist: ' + ghostpath)
            ghost = cv2.imread(ghostpath)

        # extract patch
        bbox = queryField(car_entry, 'bbox')
        roi = bbox2roi(bbox)
        patch = ghost [roi[0]:roi[2]+1, roi[1]:roi[3]+1]

        # make patch file path
        carid = queryField(car_entry, 'id')
        patchname = "%08d" % carid + IMAGE_EXT
        patchpath = op.join(out_dir, patchname)

        # resize if necessary
        if 'resize' in params.keys():
            assert (type(params['resize']) == list and len(params['resize']) == 2)
            patch = cv2.resize(patch, tuple(params['resize']))

        cv2.imwrite(patchpath, patch)

    conn.close()



def collectGhostTask (db_path, filters_path, out_dir, params = {}):
    '''
    Cluster cars and save the patches by cluster.
    Use filters to cluster and transform, and save the ghosts 
    '''

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    db_path      = op.join (CITY_DATA_PATH, db_path)
    filters_path = op.join (CITY_DATA_PATH, filters_path)
    out_dir      = op.join (CITY_DATA_PATH, out_dir)

    logging.info ('=== clustering.collectGhosts ===')
    logging.info ('db_path: '      + db_path)
    logging.info ('filters_path: ' + filters_path)
    logging.info ('out_dir: '      + out_dir)
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

    ghostfile0 = None
    for filter_group in filters_groups:
        assert ('filter' in filter_group)
        logging.info ('filter group ' + filter_group['filter'])

        cluster_dir = op.join (out_dir, filter_group['filter'])
        os.makedirs (cluster_dir)

        # get db entries
        car_entries = queryCars (cursor, filter_group)
        logging.info ('found images: ' + str(len(car_entries)))

        # write ghosts for each entry
        for car_entry in car_entries:

            # update imagefile and image
            imagefile = queryField (car_entry, 'imagefile')
            cursor.execute('SELECT ghostfile FROM images WHERE imagefile=?', (imagefile,))
            (ghostfile,) = cursor.fetchone()
            ghostpath = op.join (os.getenv('CITY_DATA_PATH'), ghostfile)
            if ghostfile0 is None or ghostfile0 != ghostfile:
                logging.debug ('update image from ' + ghostfile)
                ghostfile0 = ghostfile
                if not op.exists (ghostpath):
                    raise Exception ('ghostpath does not exist: ' + ghostpath)
                ghost = cv2.imread(ghostpath)

            carid, patch = getGhost (car_entry, ghost)

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
        readme.write('with filters \n' + json.dumps(filters_groups, indent=4) + '\n')



def writeInfoFile (db_path, filters_path, out_dir, params = {}):

    logging.info ('==== writeInfoFile ====')
    logging.info ('db_path: '      + db_path)
    logging.info ('filters_path: ' + filters_path)
    logging.info ('out_dir: '      + out_dir)
    logging.info ('params: ' + str(params))

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    db_path      = op.join(CITY_DATA_PATH, db_path)
    filters_path = op.join(CITY_DATA_PATH, filters_path)
    out_dir      = op.join(CITY_DATA_PATH, out_dir)

    dupl_num = params['dupl_num'] if 'dupl_num' in params.keys() else 1

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
            filter_group_im = dict(filter_group)

            if not 'constraint' in filter_group_im.keys():
                filter_group_im['constraint'] = 'WHERE imagefile="' + imagefile + '"'
            else:
                filter_group_im['constraint'] += ' AND imagefile="' + imagefile + '"'

            # get db entries
            car_entries = queryCars (cursor, filter_group_im)
            counter += len(car_entries)

            # skip if there are no objects
            if not car_entries:
                continue

            ghostpath = op.join (os.getenv('CITY_DATA_PATH'), ghostfile)
            info_file.write (op.relpath(ghostpath, out_dir))
            info_file.write (' ' + str(len(car_entries)))

            for car_entry in car_entries:
                bbox = queryField(car_entry, 'bbox')
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
        readme.write('with filters \n' + json.dumps(filters_groups, indent=4) + '\n')



def patches2datFile (dir_in, dat_out_path):

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    dir_in       = op.join(CITY_DATA_PATH, dir_in)
    dat_out_path = op.join(CITY_DATA_PATH, dat_out_path)

    image_paths = glob.glob(op.join(dir_in, '*.png'))
    logging.info ('found ' + str(len(image_paths)) + ' files')

    with open(dat_out_path, 'w') as dat_file:
        for image_path in image_paths:
            img = cv2.imread(image_path)
            assert (img is not None)
            (height,width,depth) = img.shape
            str_roi = '  1  0 0 ' + str(width) + ' ' + str(height)
            dat_file.write( op.relpath(image_path, op.dirname(dat_out_path)) + str_roi + '\n')




