import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
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
        createDb(self.conn)

    def tearDown (self):
        self.conn.close()

    def test_doesTableExist (self):
        self.assertTrue  (doesTableExist (self.conn.cursor(), 'cars'))
        self.assertTrue  (doesTableExist (self.conn.cursor(), 'images'))
        self.assertTrue  (doesTableExist (self.conn.cursor(), 'matches'))
        self.assertFalse (doesTableExist (self.conn.cursor(), 'dummy'))



class TestMicroDb (helperTesting.TestMicroDbBase):

    def test_doesTableExist (self):
        self.assertTrue  (doesTableExist(self.conn.cursor(), 'images'))
        self.assertFalse (doesTableExist(self.conn.cursor(), 'dummy'))

    def test_isColumnInTable (self):
        c = self.conn.cursor()
        self.assertTrue (isColumnInTable(c, 'images', 'width'))
        self.assertFalse (isColumnInTable(c, 'images', 'dummy_column'))
        with self.assertRaises(Exception): 
            isColumnInTable(c, 'dummy_table', 'dummy')
    
    def test_carField_normal (self):
        c = self.conn.cursor()
        # query car
        c.execute ('SELECT * FROM cars WHERE id == 1')
        car_entry = c.fetchone()
        self.assertIsNotNone (car_entry)
        # primary fields
        self.assertEqual (carField(car_entry,'id'), 1)
        self.assertEqual (carField(car_entry,'imagefile'), 'img1')
        self.assertEqual (carField(car_entry,'name'), 'sedan')
        self.assertEqual (carField(car_entry,'x1'), 24)
        self.assertEqual (carField(car_entry,'y1'), 42)
        self.assertEqual (carField(car_entry,'width'), 6)
        self.assertEqual (carField(car_entry,'height'), 6)
        self.assertEqual (carField(car_entry,'score'), 1)
        self.assertEqual (carField(car_entry,'yaw'), 180)
        self.assertEqual (carField(car_entry,'pitch'), 45)
        self.assertEqual (carField(car_entry,'color'), 'blue')
        # complex fields
        self.assertEqual (carField(car_entry,'bbox'), [24,42,6,6])
        self.assertEqual (carField(car_entry,'roi'),  [42,24,47,29])

    def test_carField_none (self):
        c = self.conn.cursor()
        # query car
        c.execute ('SELECT * FROM cars WHERE id == 2')
        car_entry = c.fetchone()
        self.assertIsNotNone (car_entry)
        # primary fields
        self.assertIsNone (carField(car_entry,'color'))

    def test_imageField (self):
        c = self.conn.cursor()
        # query image
        c.execute ('SELECT * FROM images WHERE imagefile == "img1"')
        image_entry = c.fetchone()
        self.assertIsNotNone (image_entry)
        # fields
        self.assertEqual (imageField(image_entry,'imagefile'), 'img1')
        self.assertEqual (imageField(image_entry,'width'), 100)
        self.assertEqual (imageField(image_entry,'height'), 100)
        self.assertEqual (imageField(image_entry,'src'), 'src')
        self.assertEqual (imageField(image_entry,'maskfile'), 'mask1')
        self.assertEqual (imageField(image_entry,'time'), '2015-08-21 01:01:01.000')

    def test_polygonField (self):
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
        self.assertEqual (polygonField(polygon_entry,'id'), 1)
        self.assertEqual (polygonField(polygon_entry,'carid'), 1)
        self.assertEqual (polygonField(polygon_entry,'x'), 10)
        self.assertEqual (polygonField(polygon_entry,'y'), 10)



if __name__ == '__main__':
    logging.basicConfig (level=logging.ERROR)
    unittest.main()
