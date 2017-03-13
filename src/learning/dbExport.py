# dbExport aims to prepare a database collected from different sources
#   into patches dataset that can be used for training/testing.
#
# dbExport cars based by orientation/size/type/color is set by user.
# The sources of objects are set in a config files.
# Format of output dataset can be different for different packages.
#

from __future__ import print_function
import os, sys, os.path as op
import abc
import logging
import shutil
import glob
import json
import sqlite3
import numpy as np
import cv2
import copy
from skimage import color
from scipy.misc import imresize
from datetime    import datetime  # to print creation timestamp in readme.txt
from helperDb    import carField, doesTableExist
from dbUtilities import bbox2roi, expandRoiFloat, mask2bbox
from helperSetup import setParamUnlessThere, assertParamIsThere, atcity
from helperImg   import ReaderVideo
from helperKeys  import KeyReaderUser


'''
Patch-helpers are responsible to write down a collection of patches.

Different patch-helper classes write patches in different formats:
  1) as a collection of image files
  2) as an hdf5 file
  3) as a numpy npz archive 

The motivation for having different classes here is that we use images for
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
        setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
        self.relpath = params['relpath']


    def initDataset (self, name, params = {}):

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

        self.roi_path = op.join(self.out_dir, 'roi.txt')
        self.f_roi = open(self.roi_path, 'w')
        logging.debug ('writing rois to %s' % self.roi_path)


    def closeDataset (self):
        self.f_ids.close()
        self.f_label.close()
        self.f_roi.close()


    def writePatch (self, patch, carid, label = None, mask = None, roi = None):
        logging.debug ('writing carid #%d' % carid)
        assert len(patch.shape) == 3 and patch.shape[2] == 3
        patchfile = op.join (self.out_dir, '%08d.jpg' % carid)
        cv2.imwrite (patchfile, patch)
        self.f_ids.write ('%08d\n' % carid)
        if label is not None:
          self.f_label.write ('%08d %d\n' % (carid, label))
        if mask is not None:
          assert len(mask.shape) == 2
          assert mask.shape[:2] == patch.shape[:2]
          assert mask.dtype == np.uint8
          maskfile = op.join (self.out_dir, '%08d.png' % carid)
          cv2.imwrite (maskfile, mask)
        if roi is not None:
          self.f_roi.write ('%08d %s\n' % (carid, ' '.join([str(x) for x in roi])))


    # TODO: implement readPatch



class PatchHelperHDF5 (PatchHelperBase):

    def __init__ (self, params = {}):
        import h5py
        from helperH5 import writeNextPatch, readPatch
        setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
        self.params = params

    def initDataset (self, name, params = {}):
        setParamUnlessThere (params, 'mode', 'r')

        out_h5_path = op.join (self.params['relpath'], '%s.h5' % name)
        # remove hdf5 file if exists
        if params['mode'] == 'w':
            if op.exists (out_h5_path):
                logging.warning ('will delete existing hdf5 file: %s' % name)
                os.remove (out_h5_path)
            # create the parent directory for hdf5 file if necessary
            if not op.exists (op.dirname(out_h5_path)):
                os.makedirs (op.dirname(out_h5_path))
            logging.info ('opening hdf5 file for writing at %s' % out_h5_path)
        else:
            if not op.exists(out_h5_path):
                raise Exception ('hdf5 file %s does not exist', out_h5_path)
            logging.info ('opening hdf5 file for reading at %s' % out_h5_path)
        # create/open hdf5 file
        self.f = h5py.File (out_h5_path)

    def closeDataset (self):
        h5py.File.close (self.f)

    def writePatch (self, patch, carid, label = None):
        logging.debug ('writing carid %d' % carid)
        writeNextPatch (self.f, patch, carid, label)

    def readPatch (self):
        ''' Read next patch. Return (patch, carid, label). '''
        # increment the current index
        logging.debug ('reading patch from hdf5')
        try:
            self.patch_index += 1
        except AttributeError:
            logging.debug ('init the first patch')
            self.patch_index = 0
        # actually read patch
        logging.debug ('reading patch #%d' % self.patch_index)
        return readPatch(self.f, self.patch_index)


# the end of PatchHelper-s #


def convertFormat (in_dataset, out_dataset, params):
    '''
    Convert one image-storage format to another 
      (e.g. folder with images to hdf5 file)
    '''
    # it's a little ugly to pass essential things in parameters
    logging.info ('==== convertFormat ====')
    assertParamIsThere (params,  'in_patch_helper')
    assertParamIsThere (params, 'out_patch_helper')

    params[ 'in_patch_helper'].initDataset(in_dataset)
    params['out_patch_helper'].initDataset(out_dataset, {'mode': 'w'})

    for i in range(10000000):
        try:
            (patch, carid, label) = params['in_patch_helper'].readPatch()
            # need to write them in the same order as they wre in the hdf5
            params['out_patch_helper'].writePatch(patch, i, label)
        except:
            logging.debug ('done')
            break

    params['in_patch_helper'].closeDataset()
    params['out_patch_helper'].closeDataset()



def writeReadme (in_db_path, dataset_name, params_in = {}):
    '''
    Write info about exported dataset and params into a text file 
    '''
    params = copy.deepcopy(params_in)

    setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
    writeReadmeDir = op.join(params['relpath'], op.dirname(dataset_name))
    if not op.exists(writeReadmeDir):
        os.makedirs (writeReadmeDir)
    with open(op.join(params['relpath'], dataset_name + '.txt'), 'w') as readme:
        readme.write('from database: %s\n' % in_db_path)

        # workaround to make params writable
        if 'image_processor' in params:
            readme.write('image_processor: %s \n' % params['image_processor'])
            params.pop('image_processor', None)
        if 'patch_helper' in params:
            readme.write('patch_helper: %s \n' % params['patch_helper'])
            params.pop('patch_helper', None)
        if 'key_reader' in params:
            readme.write('key_reader: %s \n' % params['key_reader'])
            params.pop('key_reader', None)

        readme.write('with params: \n%s \n' % json.dumps(params, indent=4))



from scipy.ndimage.interpolation import rotate
from scipy.ndimage import gaussian_filter

def _distortPatch_ (image, roi, params = {}):
    '''
    Distort original patch in several ways. Default is just take original patch.
    Write down all 'number' output patches.
    Constrast +/- is not supported at the moment.
    '''
    setParamUnlessThere (params, 'number',      1)
    setParamUnlessThere (params, 'flip',        False)
    setParamUnlessThere (params, 'blur',        0)
    setParamUnlessThere (params, 'contrast',    0)
    setParamUnlessThere (params, 'color',       0)
    setParamUnlessThere (params, 'scale',       0)
    setParamUnlessThere (params, 'rotate_deg',  0)
    setParamUnlessThere (params, 'transl_perc', 0)
    setParamUnlessThere (params, 'debug',       False)
    setParamUnlessThere (params, 'key_reader',  KeyReaderUser())
    assert len(image.shape) == 3 and image.shape[2] == 3
    N = params['number']

    # trivial case
    if N == 1: return [image[roi[0]:roi[2], roi[1]:roi[3], :]]

    # take care of the borders
    # TODO: is 'edge' or 'constant' padding is better?
    #
    pad = max(roi[3]-roi[1], roi[2]-roi[0]) * 1
    padded = np.pad(image, ((pad,pad),(pad,pad),(0,0)), 'edge')
    assert padded.shape[2] == 3

    # extract a bigger patch, and make an array of them
    roiBig = [roi[0], roi[1], roi[2]+2*pad, roi[3]+2*pad]
    patch0 = padded[roiBig[0]:roiBig[2], roiBig[1]:roiBig[3], :]

    # make random modifying parameters
    flips  = np.random.choice ([False, True], size=N)
    degs   = np.random.uniform (-params['rotate_deg'], params['rotate_deg'], size=N)
    scales = np.random.uniform (-params['scale'], params['scale'], size=N)
    blurs  = abs(np.random.randn(N)) * params['blur']
    colors = np.random.uniform (-params['color'] * 255, params['color'] * 255, size=N)
    dmax   = params['transl_perc'] * pad
    dws    = np.random.uniform (low = -dmax, high = dmax, size=N)
    dhs    = np.random.uniform (low = -dmax, high = dmax, size=N)

    patches = []

    # apply modifications
    for i in range(N):
        roiSm  = [pad, pad, patch0.shape[0]-pad, patch0.shape[1]-pad]
        patch = patch0.copy()
        if params['flip'] and flips[i]: 
            patch = np.fliplr(patch)
        if params['rotate_deg']: 
            patch = rotate (patch, degs[i], axes=(1,0), reshape=False)
        if params['blur']:
            patch = gaussian_filter(patch, sigma=blurs[i])
        if params['transl_perc']: 
            roiSm = [roiSm[0]+dhs[i], roiSm[1]+dws[i], roiSm[2]+dhs[i], roiSm[3]+dws[i]]
        if params['scale']:
            roiSm = expandRoiFloat (roiSm, patch.shape[0:2], (scales[i], scales[i]))
        if params['color']:
            patch = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
            patch[:,:,0] += colors[i].astype(np.uint8)
            patch = cv2.cvtColor(patch, cv2.COLOR_HSV2BGR)

        # crop to correct size
        patch = patch[roiSm[0]:roiSm[2], roiSm[1]:roiSm[3], :]
        if params['scale']: patch = cv2.resize(patch, (roi[3]-roi[1], roi[2]-roi[0]))

        # display patch
        if params['debug'] and ('key' not in locals() or key != 27):
            cv2.imshow('debug', patch)
            key = params['key_reader'].readKey()
            if key == 27: cv2.destroyWindow('debug')

        patches.append(patch)

    return patches


def _polygons2mask_ (c, imagefile, carid):
    '''
    Extract a mask that is saved as polygons
    (Much faster than to create a mask with dbModify.polygonsToMasks())
    '''
    c.execute('SELECT width,height FROM images WHERE imagefile = ?', (imagefile,))
    width, height = c.fetchone()

    mask = np.zeros((height, width), dtype=np.uint8)
    c.execute('SELECT x,y FROM polygons WHERE carid = ?', (carid,))
    polygon_entries = c.fetchall()
    pts = [[pt[0], pt[1]] for pt in polygon_entries]

    # trivial case
    if len(pts) < 3: return mask
    
    cv2.fillConvexPoly(mask, np.asarray(pts, dtype=np.int32), 255)
    return mask > 0


def collectPatches (c, out_dataset, params = {}):
    '''
    Save car patches into 'out_dataset', with provided label if any
    Each db entry which satisfies the provided filters is saved as an image.
    '''
    logging.info ('==== collectGhosts ====')
    assertParamIsThere  (params, 'resize') # (width,height)
    setParamUnlessThere (params, 'label',           None)
    #setParamUnlessThere (params, 'patch_helper',    PatchHelperHDF5(params))
    setParamUnlessThere (params, 'image_processor', ReaderVideo())
    assert isinstance(params['resize'], tuple) and len(params['resize']) == 2

    params['patch_helper'].initDataset(out_dataset, {'mode': 'w'})

    # write a patch for each entry
    c.execute('SELECT * FROM cars')
    car_entries = c.fetchall()
    logging.info ('found %d cars' % len(car_entries))

    for car_entry in car_entries:

        # get patch
        imagefile = carField (car_entry, 'imagefile')
        image = params['image_processor'].imread(imagefile)

        # extract patch
        roi = carField(car_entry, 'roi')
        carid = carField(car_entry, 'id')

        # crop (TODO: do so inside _distort_)
        img_patch = image[roi[0]:roi[2], roi[1]:roi[3], :]
        img_patch = cv2.resize(img_patch, params['resize'], interpolation=cv2.INTER_LINEAR)

        # get and crop the mask if exists
        c.execute('SELECT maskfile FROM images WHERE imagefile = ?', (imagefile,))
        (maskfile,) = c.fetchone()
        if doesTableExist (c, 'polygons'):
            # TODO: besides doesTableExist, check if there are polygons for that carid
            mask = _polygons2mask_ (c, imagefile, carid)
            # empirically, labelme polygon mask is too wide
            mask = cv2.erode(mask.astype(np.uint8), kernel=np.ones((3,3))).astype(bool)
        elif maskfile is not None:
            mask = params['image_processor'].maskread(maskfile)
        else:
            mask = None
        if mask is not None:  # from either polygons or maskfile
            msk_patch = mask[roi[0]:roi[2], roi[1]:roi[3]].astype(np.uint8) * 255
            msk_patch = cv2.resize(msk_patch, params['resize'], interpolation=cv2.INTER_NEAREST)
            bbox = mask2bbox(msk_patch)
            if bbox is None:
                logging.warning('carid %s has an empty bbox. Skip.')
                continue
            roi = bbox2roi(bbox)
        else:
            logging.debug('no mask or roi for imagefile %s' % imagefile)
            msk_patch = None
            roi = None

        params['patch_helper'].writePatch(img_patch, carid, params['label'], msk_patch, roi)

        # img_patches = _distortPatch_ (image, roi, params)
        # for img_patch in img_patches:

        #     # write patch
        #     img_patch = cv2.resize(img_patch, params['resize'], interpolation=cv2.INTER_LINEAR)
        #     params['patch_helper'].writePatch(img_patch, carid, params['label'])

    params['patch_helper'].closeDataset()



def collectByMatch (c, out_dataset, params = {}):
    '''
    Save car patches into 'out_dataset', labeled by matches
    Each db entry which satisfies the provided filters is saved as an image.
    '''
    logging.info ('==== collectGhosts ====')
    assertParamIsThere  (params, 'resize') # (width,height)
    setParamUnlessThere (params, 'patch_helper', PatchHelperHDF5(params))
    setParamUnlessThere (params, 'image_processor', ReaderVideo())
    assert isinstance(params['resize'], tuple) and len(params['resize']) == 2

    params['patch_helper'].initDataset(out_dataset, {'mode': 'w'})

    # if 'matches' table is empty, add a match per car
    c.execute('SELECT COUNT(*) FROM matches')
    if c.fetchone()[0] == 0:
        c.execute('SELECT id FROM cars')
        for (carid,) in c.fetchall():
            c.execute('INSERT INTO matches(match, carid) VALUES (?,?)', (carid, carid))

    # get the list of matches
    c.execute('SELECT DISTINCT(match) FROM matches')

    for (match,) in c.fetchall():
        logging.info ('processing match %d' % match)

        c.execute('''SELECT * FROM cars WHERE id IN 
                     (SELECT carid FROM matches WHERE match == ?)''', (match,))
        car_entries = c.fetchall()
        logging.info ('found %d cars' % len(car_entries))

        for car_entry in car_entries:
    
            # get patch
            imagefile = carField (car_entry, 'imagefile')
            image = params['image_processor'].imread(imagefile)

            # extract patch
            roi = carField(car_entry, 'roi')
            patches = _distortPatch_ (image, roi, params)

            for patch in patches:

                # write patch
                carid = carField(car_entry, 'id')
                patch = cv2.resize(patch, params['resize'])
                params['patch_helper'].writePatch(patch, carid, label=match)

    params['patch_helper'].closeDataset()




