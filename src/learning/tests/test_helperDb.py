import os, sys
sys.path.insert(0, os.path.abspath('..'))
import random
import logging
import sqlite3
import unittest
import helperTesting
from helperDb import *


class TestEmptyDb (unittest.TestCase):
    ''' Test that functions don't break on empty databases '''

    def setUp (self):
        self.conn = sqlite3.connect(':memory:')  # in RAM
        createDbFromConn(self.conn)

    def tearDown (self):
        self.conn.close()

    def test_checkTableExists (self):
        self.assertTrue  (checkTableExists (self.conn.cursor(), 'cars'))
        self.assertTrue  (checkTableExists (self.conn.cursor(), 'images'))
        self.assertTrue  (checkTableExists (self.conn.cursor(), 'matches'))
        self.assertFalse (checkTableExists (self.conn.cursor(), 'dummy'))



class TestMicroDb (helperTesting.TestMicroDbBase):
    
    def test_queryField_normal (self):
        c = self.conn.cursor()
        # query car
        c.execute ('SELECT * FROM cars WHERE id == 1')
        car_entry = c.fetchone()
        self.assertIsNotNone (car_entry)
        # primary fields
        self.assertEqual (queryField(car_entry,'id'), 1)
        self.assertEqual (queryField(car_entry,'imagefile'), 'img1')
        self.assertEqual (queryField(car_entry,'name'), 'sedan')
        self.assertEqual (queryField(car_entry,'x1'), 24)
        self.assertEqual (queryField(car_entry,'y1'), 42)
        self.assertEqual (queryField(car_entry,'width'), 6)
        self.assertEqual (queryField(car_entry,'height'), 6)
        self.assertEqual (queryField(car_entry,'score'), 1)
        self.assertEqual (queryField(car_entry,'yaw'), 180)
        self.assertEqual (queryField(car_entry,'pitch'), 45)
        self.assertEqual (queryField(car_entry,'color'), 'blue')
        # complex fields
        self.assertEqual (queryField(car_entry,'bbox'), [24,42,6,6])
        self.assertEqual (queryField(car_entry,'roi'),  [42,24,47,29])

    def test_queryField_none (self):
        c = self.conn.cursor()
        # query car
        c.execute ('SELECT * FROM cars WHERE id == 2')
        car_entry = c.fetchone()
        self.assertIsNotNone (car_entry)
        # primary fields
        self.assertIsNone (queryField(car_entry,'color'))

    def test_getImageField (self):
        c = self.conn.cursor()
        # query image
        c.execute ('SELECT * FROM images WHERE imagefile == "img1"')
        image_entry = c.fetchone()
        self.assertIsNotNone (image_entry)
        # fields
        self.assertEqual (getImageField(image_entry,'imagefile'), 'img1')
        self.assertEqual (getImageField(image_entry,'width'), 100)
        self.assertEqual (getImageField(image_entry,'height'), 100)
        self.assertEqual (getImageField(image_entry,'src'), 'test')
        self.assertEqual (getImageField(image_entry,'ghostfile'), 'ghost1')
        self.assertEqual (getImageField(image_entry,'maskfile'), 'mask1')
        self.assertEqual (getImageField(image_entry,'time'), '2015-08-21 01:01:01.000')

    def test_getPolygonField (self):
        c = self.conn.cursor()
        # add polygons, table and values
        createTablePolygons(c)
        s = 'polygons(id,carid,x,y)'
        v = (1,1,10,10)
        c.execute('INSERT INTO %s VALUES (?,?,?,?)' % s, v)
        # query polygon
        c.execute ('SELECT * FROM polygons WHERE id == 1')
        polygon_entry = c.fetchone()
        self.assertIsNotNone (polygon_entry)
        # fields
        self.assertEqual (getPolygonField(polygon_entry,'id'), 1)
        self.assertEqual (getPolygonField(polygon_entry,'carid'), 1)
        self.assertEqual (getPolygonField(polygon_entry,'x'), 10)
        self.assertEqual (getPolygonField(polygon_entry,'y'), 10)



if __name__ == '__main__':
    logging.basicConfig (level=logging.ERROR)
    unittest.main()
