import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import random
import logging
import sqlite3
import unittest
from learning.dbUtilities import *


class TestGammaProb (unittest.TestCase):

    def test_shape_constraint (self):
        with self.assertRaises(Exception): gammaProb(x=1, max_value=1, shape=0.5)
        with self.assertRaises(Exception): gammaProb(x=1, max_value=1, shape=1)

    def test_minus_inf (self):
        self.assertAlmostEqual (gammaProb(x=-1000, max_value=1, shape=2), 0, places=2)

    def test_plus_inf (self):
        self.assertAlmostEqual (gammaProb(x=1000, max_value=1, shape=2), 0, places=2)

    def test_most_prob (self):
        self.assertAlmostEqual (gammaProb(x=1, max_value=1, shape=2), 1, places=2)

    def test_tight (self):
        self.assertAlmostEqual (gammaProb(x=0.5, max_value=1, shape=100), 0, places=2)

    def test_normal (self):
        self.assertAlmostEqual (gammaProb(x=0.5, max_value=1, shape=2), 0.82, places=2)

    def test_loose (self):
        self.assertAlmostEqual (gammaProb(x=0.5, max_value=1, shape=1.001), 1, places=2)




class TestExpandRoi (unittest.TestCase):

    def test_expandRoiFloat_identity (self):
        roi = [3, 3, 4, 6]
        result = expandRoiFloat (roi, (10, 20), (0, 0))
        self.assertEqual (result, roi)

    def test_expandRoiFloat_expandNonInt (self):
        roi = [3, 3, 4, 6]
        result = expandRoiFloat (roi, (10, 20), (1, 0.25))
        self.assertEqual (result, [2, 3, 5, 7])

    def test_expandRoiFloat_outOfBorder (self):
        roi = [1, 17, 4, 20]
        result = expandRoiFloat (roi, (10, 20), (1, 1))
        self.assertEqual (result, [0, 12, 7, 19]);



    def test_expandRoiToRatio_expandY (self):
        roi = [3, 3, 4, 6]
        result = expandRoiToRatio (roi, (10, 20), 0, 1/1)
        self.assertEqual (result, [2, 3, 5, 6])

    def test_expandRoiToRatio_expandX (self):
        roi = [3, 3, 6, 4]
        result = expandRoiToRatio (roi, (10, 20), 0, 1/1)
        self.assertEqual (result, [3, 2, 6, 5])

    def test_expandRoiToRatio_ratioKillsXExpand (self):
        roi = [3, 3, 4, 8]
        result = expandRoiToRatio (roi, (20, 20), 1, 1/1)
        self.assertEqual (result, [1, 3, 6, 8])

    def test_expandRoiToRatio_ratioKillsYExpand (self):
        roi = [3, 3, 8, 4]
        result = expandRoiToRatio (roi, (20, 20), 1, 1/1)
        self.assertEqual (result, [3, 1, 8, 6])

    def test_expandRoiToRatio_ratioAndExpand (self):
        roi = [10, 8, 19, 21]
        result = expandRoiToRatio (roi, (100, 100), 1, 1/1)
        self.assertEqual (result, [5, 5, 24, 24])

    def test_expandRoiToRatio_ratioKillsExpandMove (self):
        roi = [1, 18, 8, 20]
        result = expandRoiToRatio (roi, (10, 20), 1, 1/1)
        self.assertEqual (result, [1, 12, 8, 19]);


class TestClustering (unittest.TestCase):

    def test_hierarchicalCluster (self):
        params = { 'cluster_threshold': 0.1 }
        centers, clusters, scores = hierarchicalClusterRoi([[1,2,10,10], [4,5,15,15], [20,20,25,25]], params)


if __name__ == '__main__':
    logging.basicConfig (level=logging.ERROR)
    unittest.main()
