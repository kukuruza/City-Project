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
import h5py
import datetime  # to print creation timestamp in readme.txt



def collectGhostsHDF5 (db_in_path, hdf5_out_path, params = {}):
    '''
    Save car ghosts as a hdf5 dataset.
    Each db entry which satisfies the provided filters is saved in the hdf5.

    Reason for making hdf5: many (100K) patches make it difficult to view and to sync
    '''
    setupHelper.setupLogHeader (db_in_path, '', params, 'collectGhostsHDF5')

    db_in_path    = op.join (os.getenv('CITY_DATA_PATH'), db_in_path)
    hdf5_out_path = op.join (os.getenv('CITY_DATA_PATH'), hdf5_out_path)

    params = setupHelper.setParamUnlessThere (params, 'write_samples', 0)
    params = setupHelper.setParamUnlessThere (params, 'constraint', '1')
    params = setupHelper.setParamUnlessThere (params, 'label', None)
    params = setupHelper.setParamUnlessThere (params, 'normalize', True)
    setupHelper.assertParamIsThere (params, 'resize')
    assert (type(params['resize']) == list and len(params['resize']) == 2)

    conn = sqlite3.connect (db_in_path)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM cars WHERE %s' % params['constraint'])
    car_entries = cursor.fetchall()
    logging.info ('found patches: ' + str(len(car_entries)))

    ghostfile0 = None

    # make data numpy array first, and write all to there
    # TODO: create dataset first and write directly to there, without a huge array in memory
    (width, height) = tuple(params['resize'])
    data = np.zeros((len(car_entries), 3, height, width), dtype='float32')
    ids  = np.zeros((len(car_entries)), dtype=int)

    # write ghosts for each entry
    for i in range(len(car_entries)):
        car_entry = car_entries[i]

        # update imagefile and image
        imagefile = queryField (car_entry, 'imagefile')
        cursor.execute('SELECT ghostfile FROM images WHERE imagefile=?', (imagefile,))
        (ghostfile,) = cursor.fetchone()
        ghostpath = op.join (os.getenv('CITY_DATA_PATH'), ghostfile)
        # ghostfile is updated only when imagefile changes (for speed)
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
        # resize
        patch = cv2.resize(patch, (width, height))

        # save a sample patch as an image
        if i < params['write_samples']:
            patchsuffix = '-id%08d%s' % (queryField(car_entry, 'id'), IMAGE_EXT)
            patchpath = op.splitext(hdf5_out_path)[0] + patchsuffix
            cv2.imwrite(patchpath, patch)

        # write to intermediate numpy arrays
        patch = np.transpose(patch.astype('float32'), (2,0,1))  # why not (1,2,0)?
        if params['normalize']: patch /= 255.
        data[i,:,:,:] = patch
        ids[i] = queryField(car_entry, 'id')

    conn.close()

    # create the hdf5
    with h5py.File(hdf5_out_path, 'w') as f:
        f['data'] = data
        f['ids']  = ids
        if params['label'] is not None: 
            try:
                f['label'] = params['label'] * np.ones((len(car_entries)), 'float32')
            except TypeError:
                logging.error('"label" in filters must be numeric')
                sys.exit()




def mergeHDF5 (h5_in_path, h5_merge_path):
    '''
    Concatenate 'h5_merge_path' to the end of 'h5_in_path'.
    Save the output as 'h5_in_path'
    '''
    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    h5_in_path    = op.join (CITY_DATA_PATH, h5_in_path)
    h5_merge_path = op.join (CITY_DATA_PATH, h5_merge_path)

    logging.info ('=== exporting.mergeHDF5 ===')
    logging.info ('h5_in_path: '    + h5_in_path)
    logging.info ('h5_merge_path: ' + h5_merge_path)

    with h5py.File(h5_in_path) as f1:
        data1 = f1['data'][:]
        ids1  = f1['ids'][:]
        label1 = f1['label'][:] if 'label' in f1 else None
        assert data1.size != 0
        assert ids1.size != 0
        assert len(ids1.shape) == 1
        assert label1 is None or len(label1.shape) == 1

    with h5py.File(h5_merge_path) as f2:
        data2 = f2['data'][:]
        ids2  = f2['ids'][:]
        label2  = f2['label'][:] if 'label' in f2 else None
        assert data2.size != 0
        assert ids2.size != 0
        assert len(ids2.shape) == 1
        assert label2 is None or len(label2.shape) == 1

    # make sure the patches have the same dimensions
    assert (list(data1.shape)[1:] == list(data2.shape)[1:])
    # make sure labels are present or not present in both files
    assert (label1 is not None and label2 is not None) or \
           (label1 is None and label2 is None)

    # TODO: if dataset are too big, need to avoid adding them in memory

    with h5py.File(h5_in_path, 'w') as fOut:
        fOut['data'] = np.vstack((data1, data2))
        fOut['ids']  = np.hstack((ids1, ids2))
        if label1 is not None: 
            fOut['label']  = np.hstack((label1, label2))
    


def collectGhostsTaskHDF5 (db_path, filters_path, out_dir, params = {}):
    '''
    Collect patches from db_path and assign labels, 
      all according to criteria in filters_path. 
    Write the collected patches and labels into an HDF5 file.
    '''

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    db_path      = op.join (CITY_DATA_PATH, db_path)
    filters_path = op.join (CITY_DATA_PATH, filters_path)
    out_dir      = op.join (CITY_DATA_PATH, out_dir)

    logging.info ('=== exporting.collectGhostsTaskHDF5 ===')
    logging.info ('db_path: '      + db_path)
    logging.info ('filters_path: ' + filters_path)
    logging.info ('out_dir: '      + out_dir)
    logging.info ('params: ' + str(params))
    logging.info ('')

    params = setupHelper.setParamUnlessThere (params, 'merge', True)

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

    # for each task, extract its own patches
    for filter_group in filters_groups:
        h5_path = op.join (out_dir, filter_group['filter'] + '.h5')

        # merge constraints from 'params' and 'filter_group'
        constraint = '1'
        if 'constraint' in filter_group.keys(): 
            assert filter_group['constraint'][0:5] != 'WHERE'  # prevent old format
            constraint += ' AND (%s)' % filter_group['constraint']
        if 'constraint' in params.keys(): 
            assert params['constraint'][0:5] != 'WHERE'  # prevent old format
            constraint += ' AND (%s)' % params['constraint']
        logging.info ('constraint: ' + constraint)
        filter_group['constraint'] = constraint

        collectGhostsHDF5 (db_path, h5_path, dict(params.items() + filter_group.items()))

    if params['merge']:
        # collect hdf5 paths into list
        h5_paths = []
        for filter_group in filters_groups:
            h5_paths.append(op.join (out_dir, filter_group['filter'] + '.h5'))
        
        # merge everything to the first h5 file
        merged_path = op.join (out_dir, op.basename(out_dir) + '.h5')
        shutil.copyfile(h5_paths[0], merged_path)
        for i in range(1, len(h5_paths)):
            mergeHDF5 (merged_path, h5_paths[i])

    # write info
    with open(op.join(out_dir, 'readme.txt'), 'w') as readme:
        if params['merge']: readme.write('merged file %s\n' % merged_path)
        readme.write('created at: %s\n' % datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y"))
        readme.write('from database %s\n' % db_path)
        readme.write('with input constraint: %s\n' % params['constraint'])
        readme.write('with filters %s\n' % json.dumps(filters_groups, indent=4))



def collectGhosts (db_in_path, out_dir, params = {}):
    '''
    Save car ghosts into out_dir. 
    Each db entry which satisfies the provided filters is saved as an image.
    '''
    setupHelper.setupLogHeader (db_in_path, '', params, 'collectGhosts')

    db_in_path = op.join (os.getenv('CITY_DATA_PATH'), db_in_path)
    out_dir    = op.join (os.getenv('CITY_DATA_PATH'), out_dir)

    params = setupHelper.setParamUnlessThere (params, 'constraint', '1')

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

    cursor.execute('SELECT * FROM cars WHERE ' + params['constraint'])
    car_entries = cursor.fetchall()
    logging.info ('found patches: ' + str(len(car_entries)))

    ghostfile0 = None

    # write ghosts for each entry
    for car_entry in car_entries:

        # update imagefile and image
        imagefile = queryField (car_entry, 'imagefile')
        cursor.execute('SELECT ghostfile FROM images WHERE imagefile=?', (imagefile,))
        (ghostfile,) = cursor.fetchone()
        ghostpath = op.join (os.getenv('CITY_DATA_PATH'), ghostfile)
        # ghostfile is updated only when imagefile changes (for speed)
        if ghostfile0 is None or ghostfile0 != ghostfile:
            logging.debug ('collectGhosts: upload new image from ' + ghostfile)
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



def collectGhostsTask (db_path, filters_path, out_dir, params = {}):
    '''
    Cluster cars and save the patches in bulk, by "task".
    Use filters to cluster and transform, and save the ghosts 
    '''

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    db_path      = op.join (CITY_DATA_PATH, db_path)
    filters_path = op.join (CITY_DATA_PATH, filters_path)
    out_dir      = op.join (CITY_DATA_PATH, out_dir)

    logging.info ('=== exporting.collectGhostsTask ===')
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

        # merge constraints from 'params' and 'filter_group'
        constraint = 'WHERE 1'
        if 'constraint' in filter_group.keys(): 
            assert filter_group['constraint'][0:5] != 'WHERE'  # prevent old format
            constraint += ' AND (%s)' % filter_group['constraint']
        if 'constraint' in params.keys(): 
            assert params['constraint'][0:5] != 'WHERE'  # prevent old format
            constraint += ' AND (%s)' % params['constraint']
        logging.info ('constraint: ' + constraint)
        filter_group['constraint'] = constraint

        # get db entries
        logging.info ('query: ' + 'SELECT * FROM cars' + constraint)
        cursor.execute('SELECT * FROM cars' + constraint)
        car_entries = cursor.fetchall()
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

            # extract patch
            bbox = queryField(car_entry, 'bbox')
            roi = bbox2roi(bbox)
            patch = ghost [roi[0]:roi[2]+1, roi[1]:roi[3]+1]

            carid = queryField(car_entry, 'id')
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
        readme.write('created at: %s\n' % datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y"))
        readme.write('from database %s\n' % db_path)
        readme.write('with input constraint: %s\n' % params['constraint'])
        readme.write('with filters %s\n' % json.dumps(filters_groups, indent=4))



def writeInfoFile (db_path, filters_path, out_dir, params = {}):
    '''
    Write .dat file for Violajones. It is a file used to produce .vec positives
    Each line corresponds to some imagefile from a dataset, may be several bboxes 
    Currently not used due to some dat -> vec problems, as far as I remember
    '''

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
    '''
    Write .dat file for Violajones. It is a file used to produce .vec positives
    Input is a bunch of patches in clustering
    It writes one bbox for each patch it gets on input.
    '''

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




