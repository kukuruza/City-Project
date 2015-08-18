import os, sys
sys.path.insert(0, os.path.abspath('..'))
import random
import logging
import sqlite3
import unittest
import helperDb
from dbEvaluate import *


class TestEmptyDb (unittest.TestCase):

    def setUp (self):
        self.conn = sqlite3.connect(':memory:')  # in RAM
        helperDb.createDbFromConn(self.conn)

    def tearDown (self):
        self.conn.close()

    def test_empties (self):
        c = self.conn.cursor()
        result = evaluateDetector (c, c, {'dist_thresh': 0.1})
        self.assertEqual (result, (0,0,0))

    def test_defaultParam (self):
        c = self.conn.cursor()
        result = evaluateDetector (c, c, {})
        self.assertEqual (result, (0,0,0))



class TestMicroDb (unittest.TestCase):

    def setUp (self):

        self.conn1 = sqlite3.connect(':memory:')  # in RAM
        helperDb.createDbFromConn(self.conn1)
        c1 = self.conn1.cursor()

        s = 'images(imagefile,width,height)'
        v = ('img1',100,100)
        c1.execute('INSERT INTO %s VALUES (?,?,?)' % s, v)
        v = ('img2',100,100)
        c1.execute('INSERT INTO %s VALUES (?,?,?)' % s, v)

        s = 'cars(imagefile,name,x1,y1,width,height)'
        v = ('img1','car1',24,42,10,10)
        c1.execute('INSERT INTO %s VALUES (?,?,?,?,?,?)' % s, v)
        v = ('img1','car2',44,62,10,10)
        c1.execute('INSERT INTO %s VALUES (?,?,?,?,?,?)' % s, v)


        self.conn2 = sqlite3.connect(':memory:')  # in RAM
        helperDb.createDbFromConn(self.conn2)
        c2 = self.conn2.cursor()

        s = 'images(imagefile,width,height)'
        v = ('img1',100,100)
        c2.execute('INSERT INTO %s VALUES (?,?,?)' % s, v)
        v = ('img2',100,100)
        c2.execute('INSERT INTO %s VALUES (?,?,?)' % s, v)

        s = 'cars(imagefile,name,x1,y1,width,height)' # 25% insters with c1.car1
        v = ('img1','car1',29,47,10,10)
        c2.execute('INSERT INTO %s VALUES (?,?,?,?,?,?)' % s, v)
        v = ('img2','car2',29,47,10,10)
        c2.execute('INSERT INTO %s VALUES (?,?,?,?,?,?)' % s, v)

    def tearDown (self):
        self.conn1.close()


    def test_sameDb (self):
        c1 = self.conn1.cursor()
        result = evaluateDetector (c1, c1, {})
        self.assertEqual (result, (2,0,0))

    def test_1to2_tough (self):
        c1 = self.conn1.cursor()
        c2 = self.conn2.cursor()
        result = evaluateDetector (c1, c2, {'dist_thresh': 0.5})
        self.assertEqual (result, (0,2,2))

    def test_1to2_loose (self):
        c1 = self.conn1.cursor()
        c2 = self.conn2.cursor()
        result = evaluateDetector (c1, c2, {'dist_thresh': 0.9})
        self.assertEqual (result, (1,1,1))

    def test_2to1_loose (self):
        c1 = self.conn1.cursor()
        c2 = self.conn2.cursor()
        result = evaluateDetector (c2, c1, {'dist_thresh': 0.9})
        self.assertEqual (result, (1,1,1))



if __name__ == '__main__':
    logging.basicConfig (level=logging.ERROR)
    unittest.main()
