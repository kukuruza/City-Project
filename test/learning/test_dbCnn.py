import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import random
import logging
import sqlite3
import unittest
from helperTesting       import TestMicroDbBase
from learning.helperDb   import createDb
from learning.helperImg  import ProcessorRandom
from learning.dbCnn      import *


# TODO: replace real model/architecture with a perceptron in testdata
network_path = 'cnn/architectures/vehicle-deploy-py.prototxt'
model_path   = 'cnn/models/vehicle_iter_20000.caffemodel'


class TestEmptyDb (unittest.TestCase):
    ''' Test that functions don't break on empty databases '''

    def setUp (self):
        # create empty db
        self.conn = sqlite3.connect(':memory:')  # in RAM
        createDb (self.conn)
        # init CNN
        self.dbCnn = DbCnn(network_path, model_path)

    def tearDown (self):
        self.conn.close()

    def test_classify(self):
        c = self.conn.cursor()
        params = {'resize': (40, 30),
                  'image_processor': ProcessorRandom({'dims': (100,100)})}
        self.dbCnn.classify (c, params)



class TestMicroDb (TestMicroDbBase):
    
    def setUp (self):
        super(TestMicroDb, self).setUp()
        # init CNN
        self.dbCnn = DbCnn(network_path, model_path)

    def tearDown (self):
        self.conn.close()


    def test_classify_dict (self):
        c = self.conn.cursor()
        params = {'resize': (40, 30),
                  'label_dict': {0: 'negative', 1: 'vehicle'},
                  'image_processor': ProcessorRandom({'dims': (100,100)})}
        self.dbCnn.classify (c, params)
        c.execute('SELECT name FROM cars')
        labels = c.fetchall()

        # note no check that predicted 'negative'
        self.assertEqual (len(labels), 3)
        for (label,) in labels:
            self.assertIn (label, ['vehicle', 'negative'])

    def test_classify_noDict (self):
        c = self.conn.cursor()
        params = {'resize': (40, 30),
                  'image_processor': ProcessorRandom({'dims': (100,100)})}
        self.dbCnn.classify (c, params)
        c.execute('SELECT name FROM cars')
        labels = c.fetchall()

        # note no check that predicted 'negative'
        self.assertEqual (len(labels), 3)
        for (label,) in labels:
            self.assertIn (label, ['0', '1'])





if __name__ == '__main__':
    logging.basicConfig (level=logging.ERROR)
    unittest.main()
