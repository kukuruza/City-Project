import os, sys
sys.path.insert(0, os.path.abspath('..'))
import random
import logging
import sqlite3
import unittest
import helperTesting
import shutil
from scipy.spatial import distance
from helperImg import *

class TestProcessorImagefile (unittest.TestCase):

    def setUp (self):
        self.processor = ProcessorImagefile ({'relpath': '.'})

    def test_readImageImpl (self):
        image = self.processor.readImageImpl ('testdata/Cassini/images/000000.jpg')
        self.assertIsNotNone (image)
        self.assertEqual (image.shape, (100, 100, 3))

    def test_readImageImpl_badImagefile (self):
        with self.assertRaises(Exception): self.processor.readImageImpl ('dummyname')

    def test_writeImageImpl (self):
        imagepath = 'testdata/test/image.jpg'
        image1 = cv2.imread('testdata/Cassini/images/000000.jpg')
        self.processor.writeImageImpl (image1, imagepath)
        image2 = cv2.imread (imagepath)
        self.assertIsNotNone (image2)
        self.assertEqual (image1.shape, image2.shape)
        dist = distance.euclidean (image1.ravel(), image2.ravel()) / image1.size
        self.assertAlmostEqual (dist, 0, 2)  # only 'almost' because of JPEG compression
        shutil.rmtree('testdata/test')

    def test_imread (self):
        image = self.processor.imread  ('testdata/Cassini/images/000000.jpg')
        self.assertIsNotNone (image)
        self.assertEqual (image.shape, (100, 100, 3))

    def test_imread_cache (self):
        ' Test that multiple read does not crash the cache. '
        image = self.processor.imread ('testdata/Cassini/images/000000.jpg')
        image = self.processor.imread ('testdata/Cassini/images/000000.jpg')
        self.assertEqual (image.shape, (100, 100, 3))
        image = self.processor.imread ('testdata/Cassini/images/000001.jpg')
        image = self.processor.imread ('testdata/Cassini/images/000001.jpg')

    def test_maskread (self):
        mask = self.processor.maskread ('testdata/Cassini/masks/000000.png')
        self.assertIsNotNone (mask)
        self.assertEqual (mask.shape, (100, 100))

    def test_maskread_cache (self):
        ' Test that multiple read does not crash the cache. '
        mask = self.processor.maskread ('testdata/Cassini/masks/000000.png')
        mask = self.processor.maskread ('testdata/Cassini/masks/000000.png')
        self.assertEqual (mask.shape, (100, 100))
        mask = self.processor.maskread ('testdata/Cassini/masks/000001.png')
        mask = self.processor.maskread ('testdata/Cassini/masks/000001.png')


    def test_imwrite (self):
        imagepath = 'testdata/test/image.jpg'
        image1 = cv2.imread('testdata/Cassini/images/000000.jpg')
        self.processor.imwrite (image1, imagepath)
        image2 = cv2.imread (imagepath)
        self.assertIsNotNone (image2)
        self.assertEqual (image1.shape, image2.shape)
        dist = distance.euclidean (image1.ravel(), image2.ravel()) / image1.size
        self.assertAlmostEqual (dist, 0, 2)  # only 'almost' because of JPEG compression
        shutil.rmtree('testdata/test')

    def test_imwrite (self):
        imagepath = 'testdata/test/mask.png'
        mask1 = cv2.imread('testdata/Cassini/masks/000000.png')
        self.processor.imwrite (mask1, imagepath)
        mask2 = cv2.imread (imagepath)
        self.assertIsNotNone (mask2)
        self.assertEqual (mask1.shape, mask2.shape)
        dist = distance.euclidean (mask1.ravel(), mask2.ravel()) / mask1.size
        self.assertAlmostEqual (dist, 0, 2)  # only 'almost' because of JPEG compression
        shutil.rmtree('testdata/test')




class TestProcessorFolder (unittest.TestCase):

    def setUp (self):
        self.processor = ProcessorFolder ({'relpath': '.'})

    def test_readImageImpl (self):
        image = self.processor.readImageImpl  ('000000.jpg', 'testdata/Cassini/images')
        self.assertIsNotNone (image)
        self.assertEqual (image.shape, (100, 100, 3))

    def test_readImageImpl_badName (self):
        with self.assertRaises(Exception): 
            self.processor.readImageImpl ('dummy', 'testdata/Cassini/images')

    def test_readImageImpl_badDataset (self):
        with self.assertRaises(Exception): 
            self.processor.readImageImpl ('dummy', 'dummydir')

    def test_writeImageImpl (self):
        image1 = cv2.imread('testdata/Cassini/images/000000.jpg')
        self.processor.writeImageImpl (image1, '000000.jpg', 'testdata/test')
        image2 = cv2.imread ('testdata/test/000000.jpg')
        self.assertIsNotNone (image2)
        self.assertEqual (image1.shape, image2.shape)
        dist = distance.euclidean (image1.ravel(), image2.ravel()) / image1.size
        self.assertAlmostEqual (dist, 0, 2)  # only 'almost' because of JPEG compression
        shutil.rmtree('testdata/test')

    def test_imread (self):
        image = self.processor.imread  (0, 'testdata/Cassini/images')
        self.assertIsNotNone (image)
        self.assertEqual (image.shape, (100, 100, 3))

    def test_imread_cache (self):
        ' Test that multiple read does not crash the cache. '
        image = self.processor.imread (0, 'testdata/Cassini/images')
        image = self.processor.imread (0, 'testdata/Cassini/images')
        self.assertEqual (image.shape, (100, 100, 3))
        image = self.processor.imread (1, 'testdata/Cassini/images')
        image = self.processor.imread (1, 'testdata/Cassini/images')

    def test_maskread (self):
        mask = self.processor.maskread (0, 'testdata/Cassini/masks')
        self.assertIsNotNone (mask)
        self.assertEqual (mask.shape, (100, 100))

    def test_maskread_cache (self):
        ' Test that multiple read does not crash the cache. '
        mask = self.processor.maskread (0, 'testdata/Cassini/masks')
        mask = self.processor.maskread (0, 'testdata/Cassini/masks')
        self.assertEqual (mask.shape, (100, 100))
        mask = self.processor.maskread (0, 'testdata/Cassini/masks')
        mask = self.processor.maskread (0, 'testdata/Cassini/masks')

    def test_imwrite (self):
        image1 = cv2.imread('testdata/Cassini/images/000000.jpg')
        self.processor.imwrite (image1, 0, 'testdata/test')
        image2 = cv2.imread ('testdata/test/000000.jpg')
        self.assertIsNotNone (image2)
        self.assertEqual (image1.shape, image2.shape)
        dist = distance.euclidean (image1.ravel(), image2.ravel()) / image1.size
        self.assertAlmostEqual (dist, 0, 2)  # only 'almost' because of JPEG compression
        shutil.rmtree('testdata/test')

    def test_maskwrite (self):
        mask1 = cv2.imread('testdata/Cassini/masks/000000.png', cv2.CV_LOAD_IMAGE_GRAYSCALE)
        self.processor.maskwrite (mask1, 0, 'testdata/test')
        mask2 = cv2.imread ('testdata/test/000000.png', -1)  # -1 for as is
        self.assertIsNotNone (mask2)
        self.assertEqual (mask1.shape, mask2.shape)
        dist = distance.euclidean (mask1.ravel(), mask2.ravel()) / mask1.size
        self.assertAlmostEqual (dist, 0, 2)  # only 'almost' because of JPEG compression
        shutil.rmtree('testdata/test')



class TestProcessorRandom (unittest.TestCase):

    def setUp (self):
        self.processor = ProcessorRandom({'dims': (100, 100)})

    def test_imread (self):
        image = self.processor.imread (image_id = None)
        self.assertIsNotNone (image)
        self.assertEqual (image.shape, (100, 100, 3))

    def test_maskread (self):
        mask = self.processor.maskread (mask_id = None)
        self.assertIsNotNone (mask)
        self.assertEqual (mask.shape, (100, 100))

    def test_imwrite (self):
        image = np.ones ((100, 100, 3)) * 128
        self.processor.imwrite (image, image_id = None)

    def test_maskwrite (self):
        mask = np.zeros ((100, 100))
        self.processor.maskwrite (mask, mask_id = None)



if __name__ == '__main__':
    logging.basicConfig (level=logging.ERROR)
    unittest.main()
