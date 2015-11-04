import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
import random
import logging
import sqlite3
import unittest
import helperTesting
import shutil
from dbFasterRcnn import *
from dbFasterRcnn import _writeXmlString_


class TestMicroDb (helperTesting.TestMicroDbBase):

    def tearDown (self):
        super(TestMicroDb, self).tearDown()

    def test_writeXmlString_ (self):
        c = self.conn.cursor()
        imagefile = 'img1'
        c.execute ('SELECT * FROM cars WHERE imagefile = ?', (imagefile,))
        car_entries = c.fetchall()
        res = _writeXmlString_ (c, imagefile, car_entries, {'out_dataset': 'out_dataset'})

    def test_writeXmlString_empty_ (self):
        c = self.conn.cursor()
        res = _writeXmlString_ (c, 'img3', [], {'out_dataset': 'out_dataset'})


    

if __name__ == '__main__':
    logging.basicConfig (level=logging.WARNING)
    unittest.main()
