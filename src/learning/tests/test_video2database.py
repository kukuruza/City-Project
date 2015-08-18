import os, sys
sys.path.insert(0, os.path.abspath('..'))
import random
import logging
import sqlite3
import unittest
import helperTesting
import shutil
from video2database import *
import helperImg


class TestVideo (unittest.TestCase):

    def setUp (self):
        self.processor = helperImg.ProcessorRandom ({'dims': (240,352), 'relpath': '.'})

    def tearDown(self):
        if op.exists('testdata/video/test'): shutil.rmtree ('testdata/video/test')


    def test_video2database (self):
        video_path    = 'testdata/video/cam119.avi'
        out_image_dir = 'testdata/video/test'
        out_db_path   = 'testdata/video/test/test.db'
        params = {'relpath': '.', 'image_processor': self.processor}
        video2database (video_path, out_image_dir, out_db_path, params)

        conn = sqlite3.connect(out_db_path)
        c = conn.cursor()
        c.execute ('SELECT * FROM images')
        image_entries = c.fetchall()
        self.assertEqual (len(image_entries), 3)
        imagefile0 = helperDb.getImageField(image_entries[0], 'imagefile')
        self.assertEqual (imagefile0, 'testdata/video/test/000000.jpg')
        imagefile2 = helperDb.getImageField(image_entries[2], 'imagefile')
        self.assertEqual (imagefile2, 'testdata/video/test/000002.jpg')
        conn.close()



if __name__ == '__main__':
    logging.basicConfig (level=logging.ERROR)
    unittest.main()