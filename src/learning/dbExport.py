# dbExport aims to prepare a database collected from different sources
#   into patches dataset that can be used for training/testing.
#
# dbExport cars based by orientation/size/type/color is set by user.
# The sources of objects are set in a config files.
# Format of output dataset can be different for different packages.
#

import abc
import logging
import os, sys
import os.path as op
import shutil
import glob
import json
import sqlite3
import numpy as np, cv2
import helperDb
from helperDb import carField
from utilities import bbox2roi
import helperSetup
import h5py
import datetime  # to print creation timestamp in readme.txt
import helperH5
import helperImg


'''
Patch-helpers are responsible to write down a collection of patches.

Different patch-helper classes write patches in different formats:
  1) as a collection of .png files or 2) as an hdf5 file.

Ability to write patches in different ways in the language of architecture
  introduces a "point of variability". That means that we want to be able
  to switch between these two classes or write another one easily.

The motivation for the point of variability here is that we use images for
  violajones and will use hdf5 format for CNN.
'''

class PatchHelperBase (object):
    ''' Declaration of interface functions '''

    @abc.abstractmethod
    def initDataset (self):
        __metaclass__ = abc.ABCMeta
        return

    @abc.abstractmethod
    def writePatch (self):
        __metaclass__ = abc.ABCMeta
        return

    @abc.abstractmethod
    def closeDataset (self):
        __metaclass__ = abc.ABCMeta
        return


class PatchHelperFolder (PatchHelperBase):

    def __init__ (self, params = {}):
        helperSetup.setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
        self.relpath = params['relpath']


    def initDataset (self, name):

        self.out_dir = op.join(self.relpath, name)
        logging.info ('creating folder at %s' % self.out_dir)
        if op.exists (self.out_dir):
            shutil.rmtree (self.out_dir)
        os.makedirs (self.out_dir)

        self.ids_path = op.join(self.out_dir, 'ids.txt')
        self.f_ids = open(self.ids_path, 'w')
        logging.debug ('writing car ids to %s' % self.ids_path)

        self.label_path = op.join(self.out_dir, 'label.txt')
        self.f_label = open(self.label_path, 'w')
        logging.debug ('writing labels to %s' % self.label_path)


    def closeDataset (self):
        self.f_ids.close()
        self.f_label.close()
        # Check if labels number is the same as ids number. 
        #   If not labels either were None or were inconsistent.
        # In any case, then remove the labels
        with open(self.ids_path) as f_ids:
            with open(self.label_path) as f_label:
                if len(f_ids.readlines()) != len(f_label.readlines()):
                    os.remove (self.label_path)


    def writePatch (self, patch, carid, label = None):
        logging.debug ('writing patch #%d' % carid)
        assert len(patch.shape) == 3 and patch.shape[2] == 3
        imagepath = op.join (self.out_dir, '%08d.png' % carid)
        cv2.imwrite (imagepath, patch)
        self.f_ids.write ('%08d\n' % carid)
        if label is not None:
            self.f_label.write ('%d\n' % label)



class PatchHelperHDF5 (PatchHelperBase):

    def __init__ (self, params = {}):
        helperSetup.setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
        self.params = params

    def initDataset (self, name):
        out_h5_path = op.join (self.params['relpath'], '%s.h5' % name)
        # remove hdf5 file if exists
        if op.exists (out_h5_path):
            os.remove (out_h5_path)
        # create the parent directory for hdf5 file if necessary
        if not op.exists (op.dirname(out_h5_path)):
            os.makedirs (op.dirname(out_h5_path))
        # create hdf5 file
        logging.info ('creating hdf5 file at %s' % out_h5_path)
        self.f = h5py.File (out_h5_path)

    def closeDataset (self):
        h5py.File.close (self.f)

    def writePatch (self, patch, carid, label = None):
        logging.debug ('writing patch #%d' % carid)
        helperH5.writeNextPatch (self.f, patch, carid, label)


# the end of PatchHelper-s #


def collectPatches (c, out_dataset, params = {}):
    '''
    Save car patches into 'out_dataset', with provided label if any
    Each db entry which satisfies the provided filters is saved as an image.
    '''
    logging.info ('==== collectGhosts ====')
    helperSetup.setParamUnlessThere (params, 'constraint', '1')
    helperSetup.setParamUnlessThere (params, 'label', None)
    helperSetup.setParamUnlessThere (params, 'patch_helper', PatchHelperHDF5(params))
    helperSetup.setParamUnlessThere (params, 'image_processor', helperImg.ProcessorImagefile())

    params['patch_helper'].initDataset(out_dataset)

    # write a patch for each entry
    c.execute('SELECT * FROM cars WHERE %s' % params['constraint'])
    for car_entry in c.fetchall():

        # get patch
        imagefile = carField (car_entry, 'imagefile')
        image = params['image_processor'].imread(imagefile)

        # extract patch
        bbox = carField(car_entry, 'bbox')
        roi = bbox2roi(bbox)
        patch = image [roi[0]:roi[2]+1, roi[1]:roi[3]+1]

        # resize if necessary. params['resize'] == (width,height)
        if 'resize' in params.keys():
            assert (isinstance(params['resize'], tuple) and len(params['resize']) == 2)
            patch = cv2.resize(patch, params['resize'])

        # write patch
        carid = carField(car_entry, 'id')
        params['patch_helper'].writePatch(patch, carid, params['label'])

    params['patch_helper'].closeDataset()


def collectByMatch (c, out_dataset, params = {}):
    '''
    Save car patches into 'out_dataset', labeled by matches
    Each db entry which satisfies the provided filters is saved as an image.
    '''
    logging.info ('==== collectGhosts ====')
    helperSetup.setParamUnlessThere (params, 'label', None)
    helperSetup.setParamUnlessThere (params, 'patch_helper', PatchHelperHDF5(params))
    helperSetup.setParamUnlessThere (params, 'image_processor', helperImg.ProcessorImagefile())

    params['patch_helper'].initDataset(out_dataset)

    # if 'matches' table is empty, add a match per car
    c.execute('SELECT COUNT(*) FROM matches')
    if c.fetchone()[0] == 0:
        c.execute('SELECT id FROM cars')
        for (carid,) in c.fetchall():
            c.execute('INSERT INTO matches(match, carid) VALUES (?,?)', (carid, carid))

    # get the list of matches
    c.execute('SELECT DISTINCT(match) FROM matches')
    match_entries = c.fetchall()

    for (match,) in match_entries:
        c.execute('''SELECT * FROM cars WHERE id IN 
                     (SELECT carid FROM matches WHERE match == ?)''', (match,))

        # write a patch for each entry
        for car_entry in c.fetchall():
    
            # get patch
            imagefile = carField (car_entry, 'imagefile')
            image = params['image_processor'].imread(imagefile)

            # extract patch
            bbox = carField(car_entry, 'bbox')
            roi = bbox2roi(bbox)
            patch = image [roi[0]:roi[2]+1, roi[1]:roi[3]+1]

            # resize if necessary. params['resize'] == (width,height)
            if 'resize' in params.keys():
                assert (isinstance(params['resize'], tuple) and len(params['resize']) == 2)
                patch = cv2.resize(patch, params['resize'])

            # write patch
            carid = carField(car_entry, 'id')
            params['patch_helper'].writePatch(patch, carid, label=match)

    params['patch_helper'].closeDataset()




# FIXME: not tested
#
def collectPatchesTask (db_path, filters_path, out_dir, params = {}):
    '''
    Cluster cars and save the patches in bulk, by "task".
    Use filters to cluster and transform, and save the patches 
    '''
    helperSetup.setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
    db_path      = op.join (params['relpath'], db_path)
    filters_path = op.join (params['relpath'], filters_path)
    out_dir      = op.join (params['relpath'], out_dir)

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
    c = conn.cursor()

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
        logging.info ('filter group %s' % filter_group['filter'])

        # merge constraints from 'params' and 'filter_group'
        constraint = 'WHERE 1'
        if 'constraint' in filter_group.keys(): 
            constraint += ' AND (%s)' % filter_group['constraint']
        if 'constraint' in params.keys(): 
            assert params['constraint'][0:5] != 'WHERE'  # prevent old format
            constraint += ' AND (%s)' % params['constraint']
        logging.info ('constraint: %s' % constraint)
        filter_group['constraint'] = constraint

        filter_params = params.copy()
        filter_params.update(filter_group)

        collectPatches (c, op.join(out_dir, filter_group['filter']), filter_params)

    conn.close()

    # write info
    with open(op.join(out_dir, 'readme.txt'), 'w') as readme:
        readme.write('created at: %s\n' % datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y"))
        readme.write('from database %s\n' % db_path)
        readme.write('with input constraint: %s\n' % params['constraint'])
        readme.write('with filters %s\n' % json.dumps(filters_groups, indent=4))



# TODO: write unittests
#
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

    db_path      = op.join(os.getenv('CITY_DATA_PATH'), db_path)
    filters_path = op.join(os.getenv('CITY_DATA_PATH'), filters_path)
    out_dir      = op.join(os.getenv('CITY_DATA_PATH'), out_dir)

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

        cursor.execute('SELECT imagefile FROM images')
        imagefiles = cursor.fetchall()

        counter = 0
        for (imagefile,) in imagefiles:
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

            imagepath = op.join (os.getenv('CITY_DATA_PATH'), imagefile)
            info_file.write (op.relpath(imagepath, out_dir))
            info_file.write (' ' + str(len(car_entries)))

            for car_entry in car_entries:
                bbox = carField(car_entry, 'bbox')
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



# TODO: write unittests
#
def patches2datFile (dir_in, dat_out_path):
    '''
    Write .dat file for Violajones. It is a file used to produce .vec positives
    Input is a bunch of patches in clustering
    It writes one bbox for each patch it gets on input.
    '''
    dir_in       = op.join(os.getenv('CITY_DATA_PATH'), dir_in)
    dat_out_path = op.join(os.getenv('CITY_DATA_PATH'), dat_out_path)

    image_paths = glob.glob(op.join(dir_in, '*.png'))
    logging.info ('found ' + str(len(image_paths)) + ' files')

    with open(dat_out_path, 'w') as dat_file:
        for image_path in image_paths:
            img = cv2.imread(image_path)
            assert (img is not None)
            (height,width,depth) = img.shape
            str_roi = '  1  0 0 ' + str(width) + ' ' + str(height)
            dat_file.write( op.relpath(image_path, op.dirname(dat_out_path)) + str_roi + '\n')
