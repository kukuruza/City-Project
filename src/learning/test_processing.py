import random
import unittest

import logging
from utilities import expandRoiFloat, expandRoiToRatio
from utilities import hierarchicalCluster


class TestExpandRoi (unittest.TestCase):

    def test_expandRoiFloat_identity (self):
        roi = [3, 3, 4, 6]
        result = expandRoiFloat (roi, (10, 20), (0, 0))
        self.assertEqual (result, roi)

    def test_expandRoiFloat_expandNonInt (self):
        roi = [3, 3, 4, 6]
        result = expandRoiFloat (roi, (10, 20), (1, 0.25))
        self.assertEqual (result, [2, 2, 5, 6])

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

    def test_expandRoiToRatio_ratioKillsExpand (self):
        roi = [3, 3, 4, 8]
        result = expandRoiToRatio (roi, (10, 20), 1, 1/1)
        self.assertEqual (result, [1, 3, 6, 8])

    def test_expandRoiToRatio_ratioAndExpand (self):
        roi = [1, 18, 8, 20]
        result = expandRoiToRatio (roi, (10, 20), 1, 1/1)
        self.assertEqual (result, [1, 12, 8, 19]);



class TestClustering (unittest.TestCase):

    def test_hierarchicalCluster (self):
        clusters = hierarchicalCluster([[1,2,10,10], [4,5,15,15], [20,20,25,25]], 0.1)
        self.assertEqual (1, 1)




if __name__ == '__main__':
    logging.basicConfig (level=logging.DEBUG)
    unittest.main()
