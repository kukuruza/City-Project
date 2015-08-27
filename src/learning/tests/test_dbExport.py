import os, sys
sys.path.insert(0, os.path.abspath('..'))
import random
import logging
import sqlite3
import unittest
import helperTesting
import shutil
from dbExport import *


class TestPatchHelperFolder (unittest.TestCase):

    def tearDown (self):
        if op.exists ('testdata/patches'): shutil.rmtree ('testdata/patches')

    def test_PatchHelperFolder (self):
        patch = np.arange (18*24*3, dtype=np.uint8)
        patch = np.reshape (patch, (18,24,3))

        patchHelper = PatchHelperFolder({'relpath': '.'})
        patchHelper.initDataset ('testdata/patches')
        patchHelper.writePatch (patch, 0, 1)
        patchHelper.writePatch (patch, 1, 1)
        patchHelper.closeDataset ()

        self.assertTrue (op.exists('testdata/patches'))
        self.assertTrue (op.exists('testdata/patches/00000000.png'))
        self.assertTrue (op.exists('testdata/patches/00000001.png'))
        self.assertTrue (op.exists('testdata/patches/ids.txt'))
        self.assertTrue (op.exists('testdata/patches/label.txt'))
        
        with open ('testdata/patches/label.txt') as f:
            lines = f.readlines()
        self.assertEqual (len(lines), 2)
        self.assertEqual (lines[0], '1\n')
        self.assertEqual (lines[1], '1\n')

        with open ('testdata/patches/ids.txt') as f:
            lines = f.readlines()
        self.assertEqual (len(lines), 2)
        self.assertEqual (lines[0], '00000000\n')
        self.assertEqual (lines[1], '00000001\n')


    def test_PatchHelperFolder_nolabel (self):
        patch = np.arange (18*24*3, dtype=np.uint8)
        patch = np.reshape (patch, (18,24,3))

        patchHelper = PatchHelperFolder({'relpath': '.'})
        patchHelper.initDataset ('testdata/patches')
        patchHelper.writePatch (patch, 0, None)
        patchHelper.writePatch (patch, 1, None)
        patchHelper.closeDataset ()

        self.assertFalse (op.exists('testdata/patches/label.txt'))



class TestPatchHelperHDF5 (unittest.TestCase):

    def tearDown (self):
        if op.exists ('testdata/patches.h5'): os.remove ('testdata/patches.h5')

    def test_TestPatchHelperHDF5 (self):
        patch = np.arange (18*24*3, dtype=np.uint8)
        patch = np.reshape (patch, (18,24,3))

        patchHelper = PatchHelperHDF5({'relpath': '.'})
        patchHelper.initDataset ('testdata/patches')
        patchHelper.writePatch (patch, 0, 1)
        patchHelper.writePatch (patch, 1, 1)
        patchHelper.closeDataset ()

        self.assertTrue (op.exists('testdata/patches.h5'))
        with h5py.File ('testdata/patches.h5') as f:
            self.assertEqual (helperH5.getNum(f), 2)
            self.assertEqual (helperH5.getImageDims(f), (18,24,3))
            self.assertEqual (helperH5.getId(f, 0), 0)
            self.assertEqual (helperH5.getId(f, 1), 1)
            self.assertEqual (helperH5.getLabel(f, 0), 1)
            self.assertEqual (helperH5.getLabel(f, 1), 1)
            image = helperH5.getImage(f, 0)
            self.assertGreaterEqual (np.min(image), 0)
            self.assertLessEqual    (np.max(image), 255)
            self.assertGreater     (np.mean(image), 100)
            self.assertLess        (np.mean(image), 150)


    def test_TestPatchHelperHDF5_nolabel (self):
        patch = np.arange (18*24*3, dtype=np.uint8)
        patch = np.reshape (patch, (18,24,3))

        patchHelper = PatchHelperHDF5({'relpath': '.'})
        patchHelper.initDataset ('testdata/patches')
        patchHelper.writePatch (patch, 0, None)
        patchHelper.writePatch (patch, 1, None)
        patchHelper.closeDataset ()

        self.assertTrue (op.exists('testdata/patches.h5'))
        with h5py.File ('testdata/patches.h5') as f:
            self.assertEqual (helperH5.getNum(f), 2)
            self.assertEqual (helperH5.getImageDims(f), (18,24,3))
            self.assertEqual (helperH5.getId(f, 0), 0)
            self.assertEqual (helperH5.getId(f, 1), 1)
            with self.assertRaises(Exception): helperH5.getLabel(f, 0)
            with self.assertRaises(Exception): helperH5.getLabel(f, 1)



class TestMicroDb (helperTesting.TestMicroDbBase):

    def tearDown (self):
        super(TestMicroDb, self).tearDown()
        if op.exists ('testdata/patches'): shutil.rmtree ('testdata/patches')
        if op.exists ('testdata/patches.h5'): os.remove ('testdata/patches.h5')


    def test_collectPatches_hdf5 (self):
        out_dataset = 'testdata/patches'
        patchHelper = PatchHelperHDF5({'relpath': '.'})
        imageProcessor = helperImg.ProcessorRandom({'dims': (100,100)})
        params = {'image_processor': imageProcessor, 'patch_helper': patchHelper, 'resize': (24,18)}
        collectPatches (self.conn.cursor(), out_dataset, params)

        self.assertTrue (op.exists('testdata/patches.h5'))
        with h5py.File ('testdata/patches.h5') as f:
            self.assertEqual (helperH5.getNum(f), 3)
            self.assertEqual (helperH5.getImageDims(f), (18,24,3))


    def test_collectPatches_folder (self):
        out_dataset = 'testdata/patches'
        patchHelper = PatchHelperFolder({'relpath': '.'})
        imageProcessor = helperImg.ProcessorRandom({'dims': (100,100)})
        params = {'image_processor': imageProcessor, 'patch_helper': patchHelper, 'resize': (24,18)}
        collectPatches (self.conn.cursor(), out_dataset, params)

        self.assertTrue (op.exists('testdata/patches'))
        self.assertTrue (op.exists('testdata/patches/00000001.png'))
        self.assertTrue (op.exists('testdata/patches/00000002.png'))
        self.assertTrue (op.exists('testdata/patches/00000003.png'))
        self.assertTrue (op.exists('testdata/patches/ids.txt'))
        self.assertFalse(op.exists('testdata/patches/label.txt'))


    def test_collectPatches_hdf5_constraint (self):
        out_dataset = 'testdata/patches'
        patchHelper = PatchHelperHDF5({'relpath': '.'})
        imageProcessor = helperImg.ProcessorRandom({'dims': (100,100)})
        params = {'image_processor': imageProcessor, 'patch_helper': patchHelper, 'resize': (24,18)}
        params['constraint'] = 'name = "truck"'
        collectPatches (self.conn.cursor(), out_dataset, params)

        self.assertTrue (op.exists('testdata/patches.h5'))
        with h5py.File ('testdata/patches.h5') as f:
            self.assertEqual (helperH5.getNum(f), 2)
            self.assertEqual (helperH5.getImageDims(f), (18,24,3))


    def test_collectPatches_folder_constraint (self):
        out_dataset = 'testdata/patches'
        patchHelper = PatchHelperFolder({'relpath': '.'})
        imageProcessor = helperImg.ProcessorRandom({'dims': (100,100)})
        params = {'image_processor': imageProcessor, 'patch_helper': patchHelper, 'resize': (24,18)}
        params['constraint'] = 'name = "truck"'
        collectPatches (self.conn.cursor(), out_dataset, params)

        self.assertTrue (op.exists('testdata/patches'))
        self.assertFalse(op.exists('testdata/patches/00000001.png'))
        self.assertTrue (op.exists('testdata/patches/00000002.png'))
        self.assertTrue (op.exists('testdata/patches/00000003.png'))
        self.assertTrue (op.exists('testdata/patches/ids.txt'))
        self.assertFalse(op.exists('testdata/patches/label.txt'))


    

if __name__ == '__main__':
    logging.basicConfig (level=logging.ERROR)
    unittest.main()
