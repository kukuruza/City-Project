import os, sys, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'test/learning'))
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/backend'))
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
import random
import logging
import sqlite3
import unittest
import helperTesting
import shutil
from scipy.spatial import distance
from helperImg import *


class TestReaderVideo (unittest.TestCase):

    def setUp (self):
        self.reader = ReaderVideo ({'relpath': '.'})

    def _compareImages_ (self, src, trg):
        self.assertIsNotNone (src)
        self.assertEqual (src.dtype, trg.dtype)
        self.assertEqual (src.shape, trg.shape)
        diff = np.abs(src.astype(int) - trg.astype(int))
        self.assertAlmostEqual (np.mean(diff) / 255.0, 0, 1)
        #cv2.imshow('show', np.hstack((src, trg)))
        #cv2.waitKey(-1)
        # TODO: why for these tiny images image1read has artifacts on the right side??

    def test_readImpl_sequence (self):
        image1read = self.reader.readImpl ('testdata/Cassini/images/000000dummy', False)
        image1true = cv2.imread                ('testdata/Cassini/images/000000.jpg')
        self._compareImages_ (image1read, image1true)
        image2read = self.reader.readImpl ('testdata/Cassini/images/000001dummy', False)
        image2true = cv2.imread                ('testdata/Cassini/images/000001.jpg')
        self._compareImages_ (image2read, image2true)
        self.assertEqual (len(self.reader.image_video), 1)
        self.assertTrue ('testdata/Cassini/images.avi' in self.reader.image_video)

    def test_readImpl_inverseSequence (self):
        image2read = self.reader.readImpl ('testdata/Cassini/images/000001dummy', False)
        image2true = cv2.imread                ('testdata/Cassini/images/000001.jpg')
        self._compareImages_ (image2read, image2true)
        image1read = self.reader.readImpl ('testdata/Cassini/images/000000dummy', False)
        image1true = cv2.imread                ('testdata/Cassini/images/000000.jpg')
        self._compareImages_ (image1read, image1true)

    def test_readImpl_same (self):
        image2read = self.reader.readImpl ('testdata/Cassini/images/000001dummy', False)
        # repeat image2read again
        image2read = self.reader.readImpl ('testdata/Cassini/images/000001dummy', False)
        image2true = cv2.imread                ('testdata/Cassini/images/000001.jpg')
        self._compareImages_ (image2read, image2true)

    def test_readImpl_badPath (self):
        with self.assertRaises(Exception): 
            self.reader.readImpl ('dummy/path', False)

    def test_readImpl_badImageid (self):
        with self.assertRaises(Exception): 
            self.reader.readImpl ('testdata/Cassini/images/100', False)


    def test_imread_sequence (self):
        image1read = self.reader.imread ('testdata/Cassini/images/000000dummy')
        image1true = cv2.imread         ('testdata/Cassini/images/000000.jpg')
        self._compareImages_ (image1read, image1true)
        image2read = self.reader.imread ('testdata/Cassini/images/000001dummy')
        image2true = cv2.imread         ('testdata/Cassini/images/000001.jpg')
        self._compareImages_ (image2read, image2true)

    def test_imread_cache (self):
        image2read = self.reader.imread ('testdata/Cassini/images/000001dummy')
        image2true = cv2.imread         ('testdata/Cassini/images/000001.jpg')
        self.assertTrue ('testdata/Cassini/images/000001dummy' in self.reader.image_cache)
        image2cached = self.reader.image_cache['testdata/Cassini/images/000001dummy']
        self._compareImages_ (image2cached, image2true)
        image2read = self.reader.imread ('testdata/Cassini/images/000001dummy')
        self._compareImages_ (image2read, image2true)

    def test_imread_twoVideos (self):
        image2read = self.reader.imread ('testdata/Cassini/images/000001dummy')
        image5read = self.reader.imread ('testdata/Moon/images/000002dummy')
        image5true = cv2.imread         ('testdata/Moon/images/000002.jpg')
        self._compareImages_ (image5read, image5true)
        image1read = self.reader.imread ('testdata/Cassini/images/000000dummy')
        image1true = cv2.imread         ('testdata/Cassini/images/000000.jpg')
        self._compareImages_ (image1read, image1true)
        image3read = self.reader.imread ('testdata/Moon/images/000000dummy')
        image3true = cv2.imread         ('testdata/Moon/images/000000.jpg')
        self._compareImages_ (image3read, image3true)
        self.assertTrue ('testdata/Moon/images/000000dummy' in self.reader.image_cache)
        self.assertEqual (len(self.reader.image_video), 2)
        self.assertTrue ('testdata/Cassini/images.avi' in self.reader.image_video)
        self.assertTrue ('testdata/Moon/images.avi'    in self.reader.image_video)


    def test_maskread_sequence (self):
        mask1read = self.reader.maskread ('testdata/Cassini/masks/000000dummy')
        mask1true = cv2.imread           ('testdata/Cassini/masks/000000.png', 0)
        mask1true = (mask1true > 127)
        self._compareImages_ (mask1read, mask1true)
        mask2read = self.reader.maskread ('testdata/Cassini/masks/000001dummy')
        mask2true = cv2.imread           ('testdata/Cassini/masks/000001.png', 0)
        mask2true = (mask2true > 127)
        self._compareImages_ (mask2read, mask2true)

    def test_maskread_cache (self):
        mask2read = self.reader.maskread ('testdata/Cassini/masks/000001dummy')
        mask2true = cv2.imread           ('testdata/Cassini/masks/000001.png', 0)
        mask2true = (mask2true > 127)
        self.assertTrue ('testdata/Cassini/masks/000001dummy' in self.reader.mask_cache)
        mask2cached = self.reader.mask_cache['testdata/Cassini/masks/000001dummy']
        self._compareImages_ (mask2cached, mask2true)
        mask2read = self.reader.maskread ('testdata/Cassini/masks/000001dummy')
        self._compareImages_ (mask2read, mask2true)

    def test_maskread_twoVideos (self):
        mask2read = self.reader.maskread ('testdata/Cassini/masks/000001dummy')
        mask5read = self.reader.maskread ('testdata/Moon/masks/000002dummy')
        mask5true = cv2.imread           ('testdata/Moon/masks/000002.png', 0)
        mask5true = (mask5true > 127)
        self._compareImages_ (mask5read, mask5true)
        mask1read = self.reader.maskread ('testdata/Cassini/masks/000000dummy')
        mask1true = cv2.imread           ('testdata/Cassini/masks/000000.png', 0)
        mask1true = (mask1true > 127)
        self._compareImages_ (mask1read, mask1true)
        mask3read = self.reader.maskread ('testdata/Moon/masks/000000dummy')
        mask3true = cv2.imread           ('testdata/Moon/masks/000000.png', 0)
        mask3true = (mask3true > 127)
        self._compareImages_ (mask3read, mask3true)
        self.assertTrue ('testdata/Moon/masks/000000dummy' in self.reader.mask_cache)
        self.assertEqual (len(self.reader.mask_video), 2)
        self.assertTrue ('testdata/Cassini/masks.avi' in self.reader.mask_video)
        self.assertTrue ('testdata/Moon/masks.avi'    in self.reader.mask_video)


class TestProcessorVideo (unittest.TestCase):

    def setUp (self):
        self.processor = ProcessorVideo \
           ({'relpath': '.', 
             'out_dataset': {'testdata/Cassini/images.avi': 'testdata/Cassini/imwrite.avi',
                             'testdata/Cassini/masks.avi': 'testdata/Cassini/maskwrite.avi',
                             'testdata/Moon/images.avi': 'testdata/Moon/imwrite.avi',
                             'testdata/Moon/masks.avi': 'testdata/Moon/maskwrite.avi'}
            })

    def tearDown (self):
        if op.exists('testdata/Cassini/imwrite.avi'): os.remove('testdata/Cassini/imwrite.avi')
        if op.exists('testdata/Cassini/maskwrite.avi'): os.remove('testdata/Cassini/maskwrite.avi')
        if op.exists('testdata/Moon/imwrite.avi'): os.remove('testdata/Moon/imwrite.avi')
        if op.exists('testdata/Moon/maskwrite.avi'): os.remove('testdata/Moon/maskwrite.avi')

    def _compareImages_ (self, src, trg):
        self.assertIsNotNone (src)
        self.assertEqual (src.shape, trg.shape)
        diff = np.abs(src.astype(int) - trg.astype(int))
        self.assertAlmostEqual (np.mean(diff) / 255.0, 0, 1)
        #cv2.imshow('show', np.hstack((src, trg)))
        #cv2.waitKey(-1)
        # TODO: why for these tiny images image1read has artifacts on the right side??

    def test_writeImpl_sequence (self):
        image1read = self.processor.readImpl ('testdata/Cassini/images/000000', False)
        self.processor.writeImpl (image1read, 'testdata/Cassini/images/000000', False)
        self.assertEqual (len(self.processor.frame_size), 1)
        self.assertEqual (len(self.processor.out_image_video), 1)
        self.assertEqual (self.processor.frame_size['testdata/Cassini/imwrite.avi'], (100, 100))

        image2read = self.processor.readImpl ('testdata/Cassini/images/000001', False)
        self.processor.writeImpl (image1read, 'testdata/Cassini/images/000001', False)
        self.assertEqual (len(self.processor.frame_size), 1)
        self.assertEqual (len(self.processor.out_image_video), 1)
        self.assertEqual (self.processor.frame_size['testdata/Cassini/imwrite.avi'], (100, 100))

    def test_writeImpl_twoVideos (self):
        image1read = self.processor.readImpl ('testdata/Cassini/images/000000', False)
        self.processor.writeImpl (image1read, 'testdata/Cassini/images/000000', False)
        image2read = self.processor.readImpl ('testdata/Moon/images/000000', False)
        self.processor.writeImpl (image2read, 'testdata/Moon/images/000000', False)
        self.assertEqual (len(self.processor.frame_size), 2)
        self.assertEqual (len(self.processor.out_image_video), 2)

        image3read = self.processor.readImpl ('testdata/Cassini/images/000001', False)
        self.processor.writeImpl (image3read, 'testdata/Cassini/images/000001', False)
        image4read = self.processor.readImpl ('testdata/Moon/images/000001', False)
        self.processor.writeImpl (image4read, 'testdata/Moon/images/000001', False)
        self.assertEqual (len(self.processor.frame_size), 2)
        self.assertEqual (len(self.processor.out_image_video), 2)

    def test_writeImpl_badFramesize (self):
        image1read = self.processor.readImpl ('testdata/Cassini/images/000000', False)
        image2read = self.processor.readImpl ('testdata/Moon/images/000000', False)
        with self.assertRaises (Exception):
            self.processor.writeImpl (image1read, 'testdata/Moon/images/000000', False)

    def test_writeImpl_badFramesize (self):
        image1read = self.processor.readImpl ('testdata/Cassini/images/000000', False)
        with self.assertRaises (Exception):
            self.processor.writeImpl (image1read, 'testdata/Moon/images/000000', False)

    def test_writeImpl_existingVideofile (self):
        open('testdata/Cassini/empty.avi', 'a').close()  # create empty dummy file
        self.processor = ProcessorVideo \
           ({'relpath': '.', 
             'out_dataset': {'testdata/Cassini/images.avi': 'testdata/Cassini/empty.avi'}
            })
        image1read = self.processor.readImpl ('testdata/Cassini/images/000000', False)
        with self.assertRaises (Exception):
            self.processor.writeImpl (image1read, 'testdata/Cassini/images/000000', False)
        os.remove('testdata/Cassini/empty.avi')  # remove this dummy file

    # TURNED OFF. Necessary for writing augmentation videos
    # def test_writeImpl_notFirst (self):
    #     image = self.processor.readImpl ('testdata/Moon/images/000002', False)
    #     with self.assertRaises (Exception):
    #         self.processor.writeImpl (image, 'testdata/Moon/images/000002', False)

    # TURNED OFF. Necessary for writing augmentation videos
    # def test_writeImpl_nonSequential (self):
    #     image = self.processor.readImpl ('testdata/Moon/images/000000', False)
    #     self.processor.writeImpl (image, 'testdata/Moon/images/000000', False)
    #     image = self.processor.readImpl ('testdata/Moon/images/000002', False)
    #     with self.assertRaises (Exception):
    #         self.processor.writeImpl (image, 'testdata/Moon/images/000002', False)


    def test_imwrite (self):
        image1read = self.processor.imread ('testdata/Cassini/images/000000')
        self.processor.imwrite (image1read, 'testdata/Cassini/images/000000')
        image2read = self.processor.imread ('testdata/Moon/images/000000')
        self.processor.imwrite (image2read, 'testdata/Moon/images/000000')
        #
        image3read = self.processor.imread ('testdata/Cassini/images/000001')
        self.processor.imwrite (image3read, 'testdata/Cassini/images/000001')
        image4read = self.processor.imread ('testdata/Moon/images/000001')
        self.processor.imwrite (image4read, 'testdata/Moon/images/000001')
        #
        self.processor.close()
        video = cv2.VideoCapture('testdata/Cassini/imwrite.avi')
        retval, image1saved = video.read()
        self.assertTrue (retval)
        self._compareImages_(image1read, image1saved)
        retval, image3saved = video.read()
        self.assertTrue (retval)
        self._compareImages_(image3read, image3saved)
        video.release()
        #
        self.processor.close()
        video = cv2.VideoCapture('testdata/Moon/imwrite.avi')
        retval, image2saved = video.read()
        self.assertTrue (retval)
        self._compareImages_(image2read, image2saved)
        retval, image4saved = video.read()
        self.assertTrue (retval)
        self._compareImages_(image4read, image4saved)
        video.release()

    def test_maskwrite (self):
        mask1read = self.processor.maskread ('testdata/Cassini/masks/000000')
        self.processor.maskwrite (mask1read, 'testdata/Cassini/masks/000000')
        mask2read = self.processor.maskread ('testdata/Moon/masks/000000')
        self.processor.maskwrite (mask2read, 'testdata/Moon/masks/000000')
        #
        mask3read = self.processor.maskread ('testdata/Cassini/masks/000001')
        self.processor.maskwrite (mask3read, 'testdata/Cassini/masks/000001')
        mask4read = self.processor.maskread ('testdata/Moon/masks/000001')
        self.processor.maskwrite (mask4read, 'testdata/Moon/masks/000001')
        #
        self.processor.close()
        video = cv2.VideoCapture('testdata/Cassini/maskwrite.avi')
        retval, mask1saved = video.read()
        mask1saved = mask1saved > 127
        self.assertTrue (retval)
        self._compareImages_(mask1read, mask1saved[:,:,0])
        retval, mask3saved = video.read()
        mask3saved = mask3saved > 127
        self.assertTrue (retval)
        self._compareImages_(mask3read, mask3saved[:,:,0])
        video.release()
        #
        self.processor.close()
        video = cv2.VideoCapture('testdata/Moon/maskwrite.avi')
        retval, mask2saved = video.read()
        mask2saved = mask2saved > 127
        self.assertTrue (retval)
        self._compareImages_(mask2read, mask2saved[:,:,0])
        retval, mask4saved = video.read()
        mask4saved = mask4saved > 127
        self.assertTrue (retval)
        self._compareImages_(mask4read, mask4saved[:,:,0])
        video.release()






class TestProcessorImagefile (unittest.TestCase):

    def setUp (self):
        self.processor = ProcessorImagefile ({'relpath': '.'})

    def test_readImpl (self):
        image = self.processor.readImpl ('testdata/Cassini/images/000000.jpg')
        self.assertIsNotNone (image)
        self.assertEqual (image.shape, (100, 100, 3))

    def test_readImpl_badImagefile (self):
        with self.assertRaises(Exception): self.processor.readImpl ('dummyname')

    def test_writeImpl (self):
        image1 = cv2.imread('testdata/Cassini/images/000000.jpg')
        imagepath = 'testdata/test/image.jpg'
        self.processor.writeImpl (image1, imagepath)
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

    def test_maskwrite (self):
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

    def test_readImpl (self):
        image = self.processor.readImpl  ('000000.jpg', 'testdata/Cassini/images')
        self.assertIsNotNone (image)
        self.assertEqual (image.shape, (100, 100, 3))

    def test_readImpl_badName (self):
        with self.assertRaises(Exception): 
            self.processor.readImpl ('dummy', 'testdata/Cassini/images')

    def test_readImpl_badDataset (self):
        with self.assertRaises(Exception): 
            self.processor.readImpl ('dummy', 'dummydir')

    def test_writeImpl (self):
        image1 = cv2.imread('testdata/Cassini/images/000000.jpg')
        self.processor.writeImpl (image1, '000000.jpg', 'testdata/test')
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
