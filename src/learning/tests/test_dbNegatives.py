import os, sys
sys.path.insert(0, os.path.abspath('..'))
import random
import logging
import sqlite3
import unittest
import helperTesting
import shutil
from dbNegatives import *
from dbNegatives import _generateNoiseMask_, _grayCircle_, _grayMasked_, _getBboxesFromImage_


class TestMicroDb (helperTesting.TestMicroDbBase):

    def setUp (self):
        super(TestMicroDb, self).setUp()
        self.imageProcessor = helperImg.ProcessorRandom({'dims': (100,100)})
        self.params_negativeGrayspots = {'image_processor': self.imageProcessor,
                                         'blur_sigma': 2, 'noise_level': 1, 'pixelation': 20}

    # _generateNoiseMask_

    def test_generateNoiseMask__0x0 (self):
        noise = _generateNoiseMask_ ((100, 100, 3), level = 0, avg_pixelation = 0)
        self.assertIsNotNone (noise)
        self.assertEqual (noise.shape, (100, 100, 3))
        self.assertEqual (noise.dtype, float)
        self.assertEqual (np.mean(noise), 128)  # image is exactly gray

    def test_generateNoiseMask__2x0 (self):
        noise = _generateNoiseMask_ ((100, 100, 3), 2, 0)
        self.assertIsNotNone (noise)
        self.assertEqual (noise.shape, (100, 100, 3))
        self.assertEqual (noise.dtype, float)
        self.assertAlmostEqual (np.mean(noise), 128, 0)  # image is almost gray

    def test_generateNoiseMask__0x2 (self):
        noise = _generateNoiseMask_ ((100, 100, 3), 0, 2)
        self.assertIsNotNone (noise)
        self.assertEqual (noise.shape, (100, 100, 3))
        self.assertEqual (noise.dtype, float)
        self.assertAlmostEqual (np.mean(noise), 128, 0)  # image is almost gray

    def test_generateNoiseMask__2x2 (self):
        noise = _generateNoiseMask_ ((100, 100, 3), 2, 10)
        self.assertIsNotNone (noise)
        self.assertEqual (noise.shape, (100, 100, 3))
        self.assertEqual (noise.dtype, float)
        self.assertAlmostEqual (np.mean(noise), 128, 0)  # image is almost gray

    # grayspots methods

    def test_grayCircle__ (self):
        params = self.params_negativeGrayspots
        _grayCircle_ (self.conn.cursor(), 'img1', 'testdata/test', params)

    def test_grayMasked__sizemap (self):
        params = self.params_negativeGrayspots
        params['size_map_path'] = 'testdata/mapSize.tiff'
        params['relpath'] = '.'
        _grayMasked_ (self.conn.cursor(), 'img1', 'testdata/test', params)

    def test_grayMasked__width (self):
        params = self.params_negativeGrayspots
        params['width'] = 40  # cars are assumed all to be of this width
        _grayMasked_ (self.conn.cursor(), 'img1', 'testdata/test', params)

    def test_negativeGrayspots_mask_sizemap (self):
        ' Check output database after default parameters '
        c = self.conn.cursor()
        params = self.params_negativeGrayspots
        params['size_map_path'] = 'testdata/mapSize.tiff'
        params['relpath'] = '.'
        negativeGrayspots (c, 'testdata/test', params)
        shutil.rmtree('testdata/test')
        # check output db
        c.execute ('SELECT COUNT(*) FROM cars')
        self.assertEqual (c.fetchone()[0], 0)
        c.execute ('SELECT COUNT(*) FROM matches')
        self.assertEqual (c.fetchone()[0], 0)
        c.execute ('SELECT COUNT(*) FROM images')
        self.assertEqual (c.fetchone()[0], 3)
        c.execute ('SELECT ghostfile FROM images')
        ghostfiles = c.fetchall()
        self.assertEqual (ghostfiles[0][0], 'testdata/test/ghost1')
        self.assertEqual (ghostfiles[1][0], 'testdata/test/ghost2')
        self.assertEqual (ghostfiles[2][0], 'testdata/test/ghost3')

    def test_negativeGrayspots_circle (self):
        params = self.params_negativeGrayspots
        params['method'] = 'circle'
        params['relpath'] = '.'
        negativeGrayspots (self.conn.cursor(), 'testdata/test', params)
        shutil.rmtree('testdata/test')

    def test_negativeGrayspots_badmethod (self):
        params = self.params_negativeGrayspots
        params['method'] = 'bad_method'
        params['relpath'] = '.'
        with self.assertRaises(Exception): 
            negativeGrayspots (self.conn.cursor(), 'testdata/test', params)
        shutil.rmtree('testdata/test')

    # _getBboxesFromImage_

    def test_getBboxesFromImage__ (self):
        image = np.random.random ((100, 100, 3))
        bboxes = _getBboxesFromImage_ (image, 50, {})
        self.assertIsInstance (bboxes, list)
        self.assertEqual (len(bboxes), 50)
        self.assertIsInstance (bboxes[0], tuple)
        self.assertEqual (len(bboxes[0]), 4)

    def test_getBboxesFromImage__mask (self):
        # generate a 2x2 checkerboard
        mask = np.zeros ((100, 100), dtype=np.uint8)
        mask[0:50, 0:50] = 255
        mask[50:100, 50:100] = 255
        # run _getBboxesFromImage_
        image = np.random.random ((100, 100, 3))
        bboxes = _getBboxesFromImage_ (image, 50, {'mask': mask})
        self.assertIsInstance (bboxes, list)
        self.assertEqual (len(bboxes), 50)
        self.assertIsInstance (bboxes[0], tuple)
        self.assertEqual (len(bboxes[0]), 4)

    def test_getBboxesFromImage__nobboxes (self):
        ''' check that function return empty list when it's impossible to collect bboxes '''
        image = np.random.random ((100, 100, 3))
        bboxes = _getBboxesFromImage_ (image, 50, {'max_masked_perc': -0.1})
        self.assertIsInstance (bboxes, list)
        self.assertEqual (len(bboxes), 0)

    # fillNegativeDbWithBboxes

    def test_fillNegativeDbWithBboxes (self):
        c = self.conn.cursor()
        params = {'image_processor': self.imageProcessor, 'number': 50}
        fillNegativeDbWithBboxes (c, params)
        # check output db
        c.execute ('SELECT COUNT(*) FROM matches')
        self.assertEqual (c.fetchone()[0], 0)
        c.execute ('SELECT COUNT(*) FROM images')
        self.assertEqual (c.fetchone()[0], 3)
        c.execute ('SELECT COUNT(*) FROM cars')
        self.assertEqual (c.fetchone()[0], 50)
        c.execute ('SELECT COUNT(*) FROM cars WHERE imagefile == "img1"')
        self.assertGreater (c.fetchone()[0], 15)
        c.execute ('SELECT COUNT(*) FROM cars WHERE imagefile == "img2"')
        self.assertGreater (c.fetchone()[0], 15)
        c.execute ('SELECT COUNT(*) FROM cars WHERE imagefile == "img3"')
        self.assertGreater (c.fetchone()[0], 15)

    def test_fillNegativeDbWithBboxes_sizemap (self):
        c = self.conn.cursor()
        params = {'image_processor': self.imageProcessor, 'number': 50,
                  'size_map_path': 'testdata/mapSize.tiff', 'relpath': '.'}
        fillNegativeDbWithBboxes (c, params)
        c.execute ('SELECT COUNT(*) FROM cars')
        self.assertEqual (c.fetchone()[0], 50)





if __name__ == '__main__':
    logging.basicConfig (level=logging.ERROR)
    unittest.main()
