import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import random
import logging
import sqlite3
import unittest
from learning.helperKeys import KeyReaderSequence, getCalibration
from learning.helperH5   import *


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
        labels = ids.copy()
        # create in-memory hdf5 file with 'numImages' of shape WxH = 24x18
        self.f = h5py.File ('in', driver='core', backing_store=False)
        self.f.create_dataset('data',  (8,3,18,24), maxshape=(None,3,18,24))
        self.f.create_dataset('ids',   (8,1,1,1),   maxshape=(None,1,1,1))
        self.f.create_dataset('label', (8,1,1,1),   maxshape=(None,1,1,1))
        self.f['data'][:]  = data
        self.f['ids'][:]   = ids
        self.f['label'][:] = labels

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
        self.assertIsInstance (label, float)

    def test_getId (self):
        imageid = getId (self.f, 4)
        self.assertEqual (imageid, 4)
        self.assertIsInstance (imageid, int)

    def test_getImageDims (self):
        self.assertEqual (getImageDims(self.f), (18,24,3))

    def test_getNum (self):
        self.assertEqual (getNum(self.f), 8)

    def test_getNum_empty (self):
        f = h5py.File ('empty', driver='core', backing_store=False)
        self.assertEqual (getNum(f), 0)
        h5py.File.close(f)


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

    def test_writeNextPatch_noLabel (self):
        ''' Empty label should be automatically replaced with a dummy np.pi '''
        numImages = 100
        image = np.arange (18*24*3, dtype=np.uint8)
        image = np.reshape (image, (18,24,3))
        with h5py.File ('out', driver='core', backing_store=False) as out_f:
            for i in range(numImages):
                writeNextPatch (out_f, image, image_id=i, label=None)
            self.assertEqual (getNum(out_f), numImages)
            for i in range(numImages):
                self.assertAlmostEqual (getLabel(out_f, i), np.pi, places=4)


    def test_writeNextPatch_many (self):
        numImages = 2000
        image = np.arange (18*24*3, dtype=np.uint8)
        image = np.reshape (image, (18,24,3))
        with h5py.File ('out', driver='core', backing_store=False) as out_f:
            for i in range(numImages):
                writeNextPatch (out_f, image, image_id=i, label=i)


    def test_readNextPatch (self):
        (image, image_id, label) = readPatch (self.f, 1)
        self.assertEqual (image.shape, (18, 24, 3))
        self.assertEqual (label, 1)
        self.assertEqual (image_id, 1)
        (image, image_id, label) = readPatch (self.f, 0)
        self.assertEqual (image.shape, (18, 24, 3))
        self.assertEqual (label, 0)
        self.assertEqual (image_id, 0)

    def test_readNextPatch_badIndex (self):
        with self.assertRaises(Exception): readPatch (self.f, 8)


    def test_viewPatches_sequential (self):
        keys = getCalibration()
        key_sequence = 20*[keys['right']] + 20*[keys['left']] + 5*[keys['right']] + [keys['esc']]
        keyReader = KeyReaderSequence(key_sequence)
        viewPatches (self.f, params = {'key_reader': keyReader})

    def test_viewPatches_random (self):
        keys = getCalibration()
        key_sequence = 20*[keys['right']] + 20*[keys['left']]
        random.shuffle(key_sequence)
        key_sequence.append(keys['esc'])
        keyReader = KeyReaderSequence(key_sequence)
        viewPatches (self.f, params = {'random': True, 'key_reader': keyReader})


    def test_merge (self):
        # create in-memory hdf5 file for output
        with h5py.File ('out', driver='core', backing_store=False) as out_f:
            merge (self.f, self.f, out_f)
            self.assertEqual (getNum(out_f), 16)
            self.assertIsNotNone (out_f['data'][:])
            self.assertIsNotNone (out_f['label'][:])
            self.assertIsNotNone (out_f['ids'][:])
            self.assertEqual (getImageDims(out_f), (18,24,3))
            self.assertEqual (out_f['label'][:].shape, (16,1,1,1))
            self.assertEqual (out_f['ids'][:].shape,   (16,1,1,1))
            for i in range(8):
                self.assertEqual (getLabel(out_f, i), i)
                self.assertEqual (getLabel(out_f, i+8), i)

    def test_merge_toFirst (self):
        ''' 'merge' must be able to operate when in1 == out or in2 == out '''
        merge (self.f, self.f, self.f)
        self.assertEqual (getNum(self.f), 16)
        self.assertIsNotNone (self.f['data'][:])
        self.assertIsNotNone (self.f['label'][:])
        self.assertIsNotNone (self.f['ids'][:])
        self.assertEqual (getImageDims(self.f), (18,24,3))
        self.assertEqual (self.f['label'][:].shape, (16,1,1,1))
        self.assertEqual (self.f['ids'][:].shape,   (16,1,1,1))
        for i in range(8):
            self.assertEqual (getLabel(self.f, i), i)
            self.assertEqual (getLabel(self.f, i+8), i)

    def test_merge_toEmpty (self):
        ''' 'merge' must be able to add empty and add to empty dataset '''
        # create in-memory empty hdf5 file
        with h5py.File ('out', driver='core', backing_store=False) as out_f:
            merge (out_f, self.f, out_f)
            self.assertEqual (getNum(out_f), 8)
            self.assertIsNotNone (out_f['data'][:])
            self.assertIsNotNone (out_f['label'][:])
            self.assertIsNotNone (out_f['ids'][:])
            self.assertEqual (getImageDims(out_f), (18,24,3))
            self.assertEqual (out_f['label'][:].shape, (8,1,1,1))
            self.assertEqual (out_f['ids'][:].shape,   (8,1,1,1))
            for i in range(8):
                self.assertEqual (getLabel(out_f, i), i)

    def test_merge_twoEmpty (self):
        ''' 'merge' should raise exception when both inputs are empty '''
        # create in-memory empty hdf5 file
        with h5py.File ('out', driver='core', backing_store=False) as out_f:
            with self.assertRaises(Exception): merge (out_f, out_f, out_f)


    def test_multipleOf (self):
        multipleOf (self.f, multiple = 3)
        self.assertEqual (getNum(self.f), 6)
        self.assertIsNotNone (self.f['data'][:])
        self.assertIsNotNone (self.f['label'][:])
        self.assertIsNotNone (self.f['ids'][:])
        self.assertEqual (getImageDims(self.f), (18,24,3))
        self.assertEqual (self.f['label'][:].shape, (6,1,1,1))
        self.assertEqual (self.f['ids'][:].shape,   (6,1,1,1))
        for i in range(6):
            self.assertEqual (getLabel(self.f, i), getId(self.f, i))


    def test_crop (self):
        with h5py.File ('out', driver='core', backing_store=False) as out_f:
            crop (self.f, out_f, number = 3)
            self.assertEqual (getNum(out_f), 3)
            self.assertIsNotNone (out_f['data'][:])
            self.assertIsNotNone (out_f['label'][:])
            self.assertIsNotNone (out_f['ids'][:])
            self.assertEqual (getImageDims(out_f), (18,24,3))
            self.assertEqual (out_f['label'][:].shape, (3,1,1,1))
            self.assertEqual (out_f['ids'][:].shape,   (3,1,1,1))
            for i in range(3):
                self.assertEqual (getLabel(out_f, i), getId(out_f, i))

    def test_crop_toSelf (self):
        crop (self.f, self.f, number = 3)
        self.assertEqual (getNum(self.f), 3)
        self.assertIsNotNone (self.f['data'][:])
        self.assertIsNotNone (self.f['label'][:])
        self.assertIsNotNone (self.f['ids'][:])
        self.assertEqual (getImageDims(self.f), (18,24,3))
        self.assertEqual (self.f['label'][:].shape, (3,1,1,1))
        self.assertEqual (self.f['ids'][:].shape,   (3,1,1,1))
        for i in range(3):
            self.assertEqual (getLabel(self.f, i), getId(self.f, i))

    def test_crop_tooBig (self):
        with self.assertRaises(Exception): crop (self.f, self.f, number = 10)


    def test_shuffle (self):
        shuffle (self.f)
        self.assertEqual (getNum(self.f), 8)
        self.assertIsNotNone (self.f['data'][:])
        self.assertIsNotNone (self.f['label'][:])
        self.assertIsNotNone (self.f['ids'][:])
        self.assertEqual (getImageDims(self.f), (18,24,3))
        self.assertEqual (self.f['label'][:].shape, (8,1,1,1))
        self.assertEqual (self.f['ids'][:].shape,   (8,1,1,1))
        for i in range(8):
            self.assertEqual (getLabel(self.f, i), getId(self.f, i))





if __name__ == '__main__':
    logging.basicConfig (level=logging.ERROR)
    unittest.main()
