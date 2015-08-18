import os, sys
sys.path.insert(0, os.path.abspath('..'))
import random
import logging
import sqlite3
import unittest
import helperTesting
from dbManual import *
import helperImg
import helperKeys


class TestEmptyDb (unittest.TestCase):
    ''' Test that functions don't break on empty databases '''

    def setUp (self):
        self.conn = sqlite3.connect(':memory:')  # in RAM
        helperDb.createDbFromConn(self.conn)

    def tearDown (self):
        self.conn.close()

    def test_show (self):
        show (self.conn.cursor(), {})

    def test_examine (self):
        examine (self.conn.cursor(), {})

    def test_classifyName (self):
        classifyName (self.conn.cursor(), {})

    def test_classifyColor (self):
        classifyColor (self.conn.cursor(), {})

    def test_labelMatches (self):
        labelMatches (self.conn.cursor(), {})



class TestMicroDb (helperTesting.TestMicroDbBase):

    def setUp (self):
        super(TestMicroDb, self).setUp()
        self.imageProcessor = helperImg.ProcessorRandom({'dims': (100,100)})

    # show

    def test_show_all (self):
        ''' Check default parameters '''
        keyReader = helperKeys.KeyReaderSequence([32, 32, 32])
        params = {'image_processor': self.imageProcessor, 'key_reader': keyReader}
        show (self.conn.cursor(), params)

    def test_show_several (self):
        ''' Quit after the second car '''
        keyReader = helperKeys.KeyReaderSequence([32, 27])
        params = {'image_processor': self.imageProcessor, 'key_reader': keyReader}
        show (self.conn.cursor(), params)

    def test_show_imageConstraint (self):
        keyReader = helperKeys.KeyReaderSequence([32])
        imageConstr = 'imagefile = "img1"' 
        params = {'image_processor': self.imageProcessor, 'key_reader': keyReader, 'image_constraint': imageConstr}
        show (self.conn.cursor(), params)

    def test_show_carConstraint (self):
        keyReader = helperKeys.KeyReaderSequence([32, 32, 32])
        carConstr = 'name = "truck"' 
        params = {'image_processor': self.imageProcessor, 'key_reader': keyReader, 'car_constraint': carConstr}
        show (self.conn.cursor(), params)

    # examine

    def test_examine_all (self):
        ''' Check default parameters and "already the first image" '''
        keys = helperKeys.getCalibration()
        keyReader = helperKeys.KeyReaderSequence(2*[keys['right']]+3*[keys['left']]+3*[keys['right']])
        params = {'image_processor': self.imageProcessor, 'key_reader': keyReader}
        examine (self.conn.cursor(), params)

    def test_examine_several (self):
        ''' Quit after the second car '''
        keys = helperKeys.getCalibration()
        keyReader = helperKeys.KeyReaderSequence([keys['right'], 27])
        params = {'image_processor': self.imageProcessor, 'key_reader': keyReader}
        examine (self.conn.cursor(), params)

    def test_examine_carConstraint (self):
        keys = helperKeys.getCalibration()
        keyReader = helperKeys.KeyReaderSequence(2*[keys['right']])
        carConstr = 'name = "truck"' 
        params = {'image_processor': self.imageProcessor, 'key_reader': keyReader, 'car_constraint': carConstr}
        examine (self.conn.cursor(), params)

    # classifyName

    def test_classifyName_all (self):
        ''' Check default parameters '''
        keys = helperKeys.getCalibration()
        keyReader = helperKeys.KeyReaderSequence([ord('s'), ord('t'), ord('t')])
        params = {'image_processor': self.imageProcessor, 'key_reader': keyReader}
        classifyName (self.conn.cursor(), params)

    def test_classifyName_several (self):
        ''' Quit after the second car '''
        keys = helperKeys.getCalibration()
        keyReader = helperKeys.KeyReaderSequence([ord('s'), 27])
        params = {'image_processor': self.imageProcessor, 'key_reader': keyReader}
        classifyName (self.conn.cursor(), params)

    def test_classifyName_arrows (self):
        ''' Chekc navigation without assigning names and "already the first image" '''
        keys = helperKeys.getCalibration()
        keyReader = helperKeys.KeyReaderSequence(2*[keys['right']]+3*[keys['left']]+3*[keys['right']])
        params = {'image_processor': self.imageProcessor, 'key_reader': keyReader}
        classifyName (self.conn.cursor(), params)

    def test_classifyName_del (self):
        ''' Check deleting car #2. Only two cars must be left '''
        keys = helperKeys.getCalibration()
        keyReader = helperKeys.KeyReaderSequence([keys['right']]+[keys['del']]+[keys['right']])
        params = {'image_processor': self.imageProcessor, 'key_reader': keyReader}
        c = self.conn.cursor()
        classifyName (c, params)
        c.execute ('SELECT COUNT(*) FROM cars')
        self.assertEqual (c.fetchone()[0], 2)
        c.execute ('SELECT COUNT(*) FROM cars WHERE id = 2')
        self.assertEqual (c.fetchone()[0], 0)


    def test_classifyName_carConstraint (self):
        keys = helperKeys.getCalibration()
        keyReader = helperKeys.KeyReaderSequence(2*[keys['right']])
        carConstr = 'name = "truck"' 
        params = {'image_processor': self.imageProcessor, 'key_reader': keyReader, 'car_constraint': carConstr}
        classifyName (self.conn.cursor(), params)

    # classifyColor

    def test_classifyColor_all (self):
        ''' Check default parameters '''
        keys = helperKeys.getCalibration()
        keyReader = helperKeys.KeyReaderSequence([ord('g'), ord('g'), ord('g')])
        params = {'image_processor': self.imageProcessor, 'key_reader': keyReader}
        classifyColor (self.conn.cursor(), params)

    def test_classifyColor_several (self):
        ''' Quit after the second car '''
        keys = helperKeys.getCalibration()
        keyReader = helperKeys.KeyReaderSequence([ord('g'), 27])
        params = {'image_processor': self.imageProcessor, 'key_reader': keyReader}
        classifyColor (self.conn.cursor(), params)

    def test_classifyColor_arrows (self):
        ''' Chekc navigation without assigning names and "already the first image" '''
        keys = helperKeys.getCalibration()
        keyReader = helperKeys.KeyReaderSequence(2*[keys['right']]+3*[keys['left']]+3*[keys['right']])
        params = {'image_processor': self.imageProcessor, 'key_reader': keyReader}
        classifyColor (self.conn.cursor(), params)

    def test_classifyColor_del (self):
        ''' Check deleting car #2. Only two cars must be left '''
        keys = helperKeys.getCalibration()
        keyReader = helperKeys.KeyReaderSequence([keys['right']]+[keys['del']]+[keys['right']])
        params = {'image_processor': self.imageProcessor, 'key_reader': keyReader}
        c = self.conn.cursor()
        classifyColor (c, params)
        c.execute ('SELECT COUNT(*) FROM cars')
        self.assertEqual (c.fetchone()[0], 2)
        c.execute ('SELECT COUNT(*) FROM cars WHERE id = 2')
        self.assertEqual (c.fetchone()[0], 0)

    def test_classifyColor_carConstraint (self):
        keys = helperKeys.getCalibration()
        keyReader = helperKeys.KeyReaderSequence(2*[keys['right']])
        carConstr = 'name = "truck"' 
        params = {'image_processor': self.imageProcessor, 'key_reader': keyReader, 'car_constraint': carConstr}
        classifyColor (self.conn.cursor(), params)

    # matchLabel

    def test_labelMatches_arrows (self):
        ''' 
        Check navigation without labeling matches and "already the first image" 
        There are 2 image pairs
        '''
        keys = helperKeys.getCalibration()
        keyReader = helperKeys.KeyReaderSequence(1*[keys['right']]+2*[keys['left']]+2*[keys['right']])
        params = {'image_processor': self.imageProcessor, 'key_reader': keyReader}
        labelMatches (self.conn.cursor(), params)

    # TODO: need tests with mouse on matchLabel



if __name__ == '__main__':
    logging.basicConfig (level=logging.ERROR)
    unittest.main()
