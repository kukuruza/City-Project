import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
import random
import logging
import sqlite3
import unittest
import helperTesting
import shutil
from dbExport import *
from dbExport import _distortPatch_


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
            self.assertEqual (helperH5.getLabel(f, 0), int(np.pi))
            self.assertEqual (helperH5.getLabel(f, 1), int(np.pi))



class TestDistortPatch (unittest.TestCase):

    def setUp (self):
        self.Malevich = np.ones((100,100,3), dtype=np.uint8) * 255
        self.bluePatch = np.zeros((20,10,3), dtype=np.uint8)
        self.bluePatch[:,:,0] = 100
        self.Malevich[40:60,45:55,:] = self.bluePatch
        self.params = {'number': 10, 'flip': True, 'blur': 0.25, 'color': 0.05,
                       'scale': 0.1, 'rotate_deg': 10, 'transl_perc': 0.1}

    def test_distortPatch_trivial (self) :
        patches = _distortPatch_ (self.Malevich, [40,45,60,55])
        self.assertIsInstance (patches, list)
        self.assertEqual (len(patches), 1)
        self.assertTrue (np.array_equal(patches[0], self.bluePatch))

    def test_distortPatch_allOnWhite (self):
        white = np.ones((100,100,3), dtype=np.uint8) * 255
        patches = _distortPatch_ (white, [40,45,60,55], self.params)
        self.assertIsInstance (patches, list)
        self.assertEqual (len(patches), 10)
        for patch in patches:
            self.assertEqual (patch.shape, (20,10,3))
            self.assertTrue (np.mean(patch) > 250)

    def test_distortPatch_Malevich (self):
        patches = _distortPatch_ (self.Malevich, [40,45,60,55], self.params)
        self.assertIsInstance (patches, list)
        self.assertEqual (len(patches), 10)
        for patch in patches:
            self.assertTrue (patch.dtype == np.uint8)
            self.assertEqual (patch.shape, (20,10,3))
            self.assertTrue (np.mean(patch[:,:,1:2]) < 100)

    def test_distortPatch_border (self):
        white = np.ones((100,100,3), dtype=np.uint8) * 255
        patches = _distortPatch_ (white, [0,0,20,10], self.params)
        self.assertIsInstance (patches, list)
        self.assertEqual (len(patches), 10)
        for patch in patches:
            self.assertEqual (patch.shape, (20,10,3))
            self.assertTrue (np.mean(patch) > 250)

    def test_distortPatch_debugSeveral (self):
        sequence = [32, 32, 27]
        self.params['key_reader'] = helperKeys.KeyReaderSequence(sequence)
        self.params['debug'] = True
        patches = _distortPatch_ (self.Malevich, [40,45,60,55], self.params)



class TestWriteReadme (unittest.TestCase):

    def tearDown (self):
        if op.exists ('testdata/writeReadme'): shutil.rmtree ('testdata/writeReadme')

    def test_newDir (self):
        ''' 'writeReadme' should create dir tree, if does not exist '''
        writeReadme ('myDb', 'testdata/writeReadme/dummy', params = {'relpath': '.'})



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


    def test_collectPatches_hdf5_distort (self):
        out_dataset = 'testdata/patches'
        patchHelper = PatchHelperHDF5({'relpath': '.'})
        imageProcessor = helperImg.ProcessorRandom({'dims': (100,100)})
        params = {'image_processor': imageProcessor, 'patch_helper': patchHelper, 'resize': (24,18)}
        paramsDist = {'number': 10, 'flip': True, 'blur': 0.5, 'color': 0.05,
                      'scale': 0.1, 'rotate_deg': 10, 'transl_perc': 0.1}
        params.update(paramsDist)
        collectPatches (self.conn.cursor(), out_dataset, params)

        self.assertTrue (op.exists('testdata/patches.h5'))
        with h5py.File ('testdata/patches.h5') as f:
            self.assertEqual (helperH5.getNum(f), 30)
            self.assertEqual (helperH5.getImageDims(f), (18,24,3))



    def test_collectByMatch (self):
        out_dataset = 'testdata/patches'
        patchHelper = PatchHelperHDF5({'relpath': '.'})
        imageProcessor = helperImg.ProcessorRandom({'dims': (100,100)})
        params = {'image_processor': imageProcessor, 'patch_helper': patchHelper, 'resize': (24,18)}
        collectByMatch (self.conn.cursor(), out_dataset, params)

        self.assertTrue (op.exists('testdata/patches.h5'))
        with h5py.File ('testdata/patches.h5') as f:
            self.assertEqual (helperH5.getNum(f), 3)
            self.assertEqual (helperH5.getImageDims(f), (18,24,3))

            self.assertEqual (helperH5.getLabel(f, 0), 1)
            self.assertEqual (helperH5.getLabel(f, 1), 2)
            self.assertEqual (helperH5.getLabel(f, 2), 2)


    def test_collectByMatch_matchesEmpty (self):
        # clear the matches table
        self.conn.cursor().execute ('DELETE FROM matches')

        out_dataset = 'testdata/patches'
        patchHelper = PatchHelperHDF5({'relpath': '.'})
        imageProcessor = helperImg.ProcessorRandom({'dims': (100,100)})
        params = {'image_processor': imageProcessor, 'patch_helper': patchHelper, 'resize': (24,18)}
        collectByMatch (self.conn.cursor(), out_dataset, params)

        self.assertTrue (op.exists('testdata/patches.h5'))
        with h5py.File ('testdata/patches.h5') as f:
            self.assertEqual (helperH5.getNum(f), 3)
            self.assertEqual (helperH5.getImageDims(f), (18,24,3))

            self.assertEqual (helperH5.getLabel(f, 0), 1)
            self.assertEqual (helperH5.getLabel(f, 1), 2)
            self.assertEqual (helperH5.getLabel(f, 2), 3)


    def test_collectByMatch_distort (self):
        out_dataset = 'testdata/patches'
        patchHelper = PatchHelperHDF5({'relpath': '.'})
        imageProcessor = helperImg.ProcessorRandom({'dims': (100,100)})
        params = {'image_processor': imageProcessor, 'patch_helper': patchHelper, 'resize': (24,18)}
        paramsDist = {'number': 10, 'flip': True, 'blur': 0.5, 'color': 0.05,
                      'scale': 0.1, 'rotate_deg': 10, 'transl_perc': 0.1}
        params.update(paramsDist)
        collectByMatch (self.conn.cursor(), out_dataset, params)

        self.assertTrue (op.exists('testdata/patches.h5'))
        with h5py.File ('testdata/patches.h5') as f:
            self.assertEqual (helperH5.getNum(f), 30)
            self.assertEqual (helperH5.getImageDims(f), (18,24,3))


    def test_collectByMatch_constraint (self):
        out_dataset = 'testdata/patches'
        patchHelper = PatchHelperHDF5({'relpath': '.'})
        imageProcessor = helperImg.ProcessorRandom({'dims': (100,100)})
        params = {'image_processor': imageProcessor, 'patch_helper': patchHelper, 'resize': (24,18)}
        params['constraint'] = 'name = "truck"'
        paramsDist = {'number': 10, 'flip': True, 'blur': 0.5, 'color': 0.05,
                      'scale': 0.1, 'rotate_deg': 10, 'transl_perc': 0.1}
        params.update(paramsDist)
        collectByMatch (self.conn.cursor(), out_dataset, params)

        self.assertTrue (op.exists('testdata/patches.h5'))
        with h5py.File ('testdata/patches.h5') as f:
            self.assertEqual (helperH5.getNum(f), 20)
            self.assertEqual (helperH5.getImageDims(f), (18,24,3))


    

if __name__ == '__main__':
    logging.basicConfig (level=logging.ERROR)
    unittest.main()
