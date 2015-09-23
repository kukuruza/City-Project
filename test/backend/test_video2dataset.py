import os, sys, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/backend'))
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
import random
import logging
import sqlite3
import unittest
import helperTesting
import shutil
from video2dataset import _video2dataset_, exportVideo
import helperImg
import helperDb


class TestVideo (unittest.TestCase):

    def setUp (self):
        self.imgProcessor = helperImg.ProcessorRandom ({'dims': (240,352), 'relpath': '.'})

        conn = sqlite3.connect(':memory:')  # in RAM
        helperDb.createDb(conn)
        self.conn = conn

    def tearDown(self):
        if os.path.exists('testdata/video/test'): shutil.rmtree ('testdata/video/test')
        self.conn.close()


    def test_video2database_wrongTimeFormat (self):
        c = self.conn.cursor()

        video_path    = 'testdata/video/cam119.avi'
        time_path    = 'testdata/video/wrongtime.txt'
        out_image_dir = 'testdata/video/test/images'
        out_mask_dir = 'testdata/video/test/masks'
        params = {'relpath': '.', 'image_processor': self.imgProcessor}
        with self.assertRaises(Exception): 
            _video2dataset_ (c, video_path, video_path, time_path, out_image_dir, out_mask_dir, '', params)


    def test_video2database (self):
        c = self.conn.cursor()

        video_path    = 'testdata/video/cam119.avi'
        time_path    = 'testdata/video/cam119.txt'
        out_image_dir = 'testdata/video/test/images'
        out_mask_dir = 'testdata/video/test/masks'
        params = {'relpath': '.', 'image_processor': self.imgProcessor}
        _video2dataset_ (c, video_path, video_path, time_path, out_image_dir, out_mask_dir, 'test', params)

        c.execute ('SELECT * FROM images')
        image_entries = c.fetchall()
        self.assertEqual (len(image_entries), 3)
        imagefile0 = helperDb.imageField(image_entries[0], 'imagefile')
        imagefile2 = helperDb.imageField(image_entries[2], 'imagefile')
        maskfile0  = helperDb.imageField(image_entries[0], 'maskfile')
        maskfile2  = helperDb.imageField(image_entries[2], 'maskfile')
        self.assertEqual (imagefile0, 'testdata/video/test/images/000000.jpg')
        self.assertEqual (imagefile2, 'testdata/video/test/images/000002.jpg')
        self.assertEqual (maskfile0,  'testdata/video/test/masks/000000.png')
        self.assertEqual (maskfile2,  'testdata/video/test/masks/000002.png')



class TestExportVideo (unittest.TestCase):
    
    def setUp (self):
        self.conn = sqlite3.connect(':memory:')  # in RAM
        helperDb.createDb(self.conn)
        c = self.conn.cursor()

        s = 'images(imagefile,width,height)'
        v = ('testdata/Cassini/images/000000.jpg',100,100)
        c.execute('INSERT INTO %s VALUES (?,?,?)' % s, v)
        v = ('testdata/Cassini/images/000001.jpg',100,100)
        c.execute('INSERT INTO %s VALUES (?,?,?)' % s, v)
        v = ('testdata/Moon/images/000000.jpg',120,80)
        c.execute('INSERT INTO %s VALUES (?,?,?)' % s, v)
        v = ('testdata/Moon/images/000001.jpg',120,80)
        c.execute('INSERT INTO %s VALUES (?,?,?)' % s, v)
        v = ('testdata/Moon/images/000002.jpg',120,80)
        c.execute('INSERT INTO %s VALUES (?,?,?)' % s, v)

        s = 'cars(id,imagefile,name,x1,y1,width,height,score)'
        v = (1,'testdata/Cassini/images/000000.jpg','sedan',24,42,6,6,1)
        c.execute('INSERT INTO %s VALUES (?,?,?,?,?,?,?,?)' % s, v)
        v = (2,'testdata/Cassini/images/000000.jpg','truck',44,52,20,15,0.5)  # default ratio
        c.execute('INSERT INTO %s VALUES (?,?,?,?,?,?,?,?)' % s, v)
        v = (3,'testdata/Cassini/images/000001.jpg','truck',24,42,16,16,0.1)
        c.execute('INSERT INTO %s VALUES (?,?,?,?,?,?,?,?)' % s, v)

    def tearDown (self):
        if op.exists('testdata/Cassini/imwrite.avi'): os.remove('testdata/Cassini/imwrite.avi')
        if op.exists('testdata/Moon/imwrite.avi'): os.remove('testdata/Moon/imwrite.avi')


    def test_exportVideo (self):
        c = self.conn.cursor()
        image_processor = helperImg.ProcessorVideo \
           ({'relpath': '.', 
             'out_dataset': {'testdata/Cassini/images.avi': 'testdata/Cassini/imwrite.avi',
                             'testdata/Moon/images.avi': 'testdata/Moon/imwrite.avi'}
            })
        exportVideo (c, {'image_processor': image_processor, 'relpath': '.'})

        # TODO: check the videos


if __name__ == '__main__':
    logging.basicConfig (level=logging.ERROR)
    unittest.main()