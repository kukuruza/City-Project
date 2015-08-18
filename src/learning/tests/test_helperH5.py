import os, sys
sys.path.insert(0, os.path.abspath('..'))
import random
import logging
import sqlite3
import unittest
import helperTesting
from helperH5 import *


class TestHDF5 (unittest.TestCase):
    ''' A dummy .h5 is created in-memory in setUp(), and then tested. '''

    def setUp (self):
        numImages = 8
        # data
        data = np.arange (18*24*3*numImages, dtype=np.uint8)
        data = np.reshape (data, (numImages,18,24,3))
        data = np.transpose(data.astype('float32'), (0,3,1,2)) # will be NUMxCHxHxW
        data /= 255
        data -= 0.5
        # ids
        ids = np.arange (numImages, dtype=int)
        ids = np.reshape (ids, (numImages,1,1,1))
        # labels
        labels = np.arange (numImages, dtype=int)
        labels = np.reshape (labels, (numImages,1,1,1))
        # create in-memory hdf5 file with 'numImages' of shape WxH = 24x18
        self.f = h5py.File ('in', driver='core', backing_store=False)
        self.f['data']  = data
        self.f['ids']   = ids
        self.f['label'] = labels

    def tearDown (self):
        h5py.File.close(self.f)


    def test_getImage (self):
        image = getImage (self.f, 0)
        self.assertIsNotNone (image)
        self.assertEqual (image.shape, (18, 24, 3))
        self.assertEqual (image.dtype, np.uint8)
        self.assertGreater     (np.mean(image), 100)
        self.assertLess        (np.mean(image), 150)
        self.assertGreaterEqual (np.min(image), 0)
        self.assertLessEqual    (np.max(image), 255)

    def test_getLabel (self):
        label = getLabel (self.f, 4)
        self.assertEqual (label, 4)
        self.assertIsInstance (label, int)

    def test_getId (self):
        imageid = getId (self.f, 4)
        self.assertEqual (imageid, 4)
        self.assertIsInstance (imageid, int)

    def test_getImageDims (self):
        self.assertEqual (getImageDims(self.f), (18,24,3))

    def test_getNum (self):
        self.assertEqual (getNum(self.f), 8)


    def test_writeNextPatch (self):
        numImages = 100
        image = np.arange (18*24*3, dtype=np.uint8)
        image = np.reshape (image, (18,24,3))
        with h5py.File ('out', driver='core', backing_store=False) as out_f:
            for i in range(numImages):
                writeNextPatch (out_f, image, image_id=i, label=i)
            self.assertEqual (getNum(out_f), numImages)
            for i in range(numImages):
                self.assertEqual (getLabel(out_f, i), i)
            image = getImage(out_f, 0)
        self.assertGreater     (np.mean(image), 100)
        self.assertLess        (np.mean(image), 150)
        self.assertGreaterEqual (np.min(image), 0)
        self.assertLessEqual    (np.max(image), 255)


    def test_writeNextPatch_many (self):
        numImages = 2000
        image = np.arange (18*24*3, dtype=np.uint8)
        image = np.reshape (image, (18,24,3))
        with h5py.File ('out', driver='core', backing_store=False) as out_f:
            for i in range(numImages):
                writeNextPatch (out_f, image, image_id=i, label=i)

    def test_writeNextPatch_noLabel (self):
        numImages = 100
        image = np.arange (18*24*3, dtype=np.uint8)
        image = np.reshape (image, (18,24,3))
        with h5py.File ('out', driver='core', backing_store=False) as out_f:
            for i in range(numImages):
                writeNextPatch (out_f, image, image_id=i, label=None)
            self.assertEqual (getNum(out_f), numImages)
            with self.assertRaises(Exception): getLabel(out_f, 0)


    def test_viewPatches_sequential (self):
        keys = helperKeys.getCalibration()
        key_sequence = 20*[keys['right']] + 20*[keys['left']] + 5*[keys['right']] + [keys['esc']]
        keyReader = helperKeys.KeyReaderSequence(key_sequence)
        viewPatches (self.f, params = {'key_reader': keyReader})

    def test_viewPatches_random (self):
        keys = helperKeys.getCalibration()
        key_sequence = 20*[keys['right']] + 20*[keys['left']]
        random.shuffle(key_sequence)
        key_sequence.append(keys['esc'])
        keyReader = helperKeys.KeyReaderSequence(key_sequence)
        viewPatches (self.f, params = {'random': True, 'key_reader': keyReader})


    def test_mergeH5 (self):
        # create in-memory hdf5 file for output
        with h5py.File ('out', driver='core', backing_store=False) as out_f:
            mergeH5 (self.f, self.f, out_f)
            self.assertEqual (getNum(out_f), 16)
            self.assertIsNotNone (out_f['data'][:])
            self.assertIsNotNone (out_f['label'][:])
            self.assertIsNotNone (out_f['ids'][:])
            self.assertEqual (getImageDims(out_f), (18,24,3))
            self.assertEqual (out_f['label'][:].shape, (16,1,1,1))
            self.assertEqual (out_f['ids'][:].shape,   (16,1,1,1))
            self.assertEqual (getLabel(out_f, 4), 4)
            self.assertEqual (getLabel(out_f, 12), 4) # the same as label[12-8]



if __name__ == '__main__':
    logging.basicConfig (level=logging.ERROR)
    unittest.main()
