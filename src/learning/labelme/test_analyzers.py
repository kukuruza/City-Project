import random
import unittest

import logging
from analyzers import BaseAnalyzer


class TestBaseAnalyzer (unittest.TestCase):

    def setUp (self):
        self.analyzer = BaseAnalyzer ()

    def test_expandRoiFloat_identity (self):
        roi = [3, 3, 4, 6]
        result = self.analyzer.expandRoiFloat(roi, (10, 20), (0, 0))
        self.assertEqual (result, roi)

    def test_expandRoiFloat_expandNonInt (self):
        roi = [3, 3, 4, 6]
        result = self.analyzer.expandRoiFloat(roi, (10, 20), (1, 0.25))
        self.assertEqual (result, [2, 2, 5, 6])

    def test_expandRoiFloat_outOfBorder (self):
        roi = [1, 17, 4, 20]
        result = self.analyzer.expandRoiFloat(roi, (10, 20), (1, 1))
        self.assertEqual (result, [0, 12, 7, 19]);



    def test_expandRoiToRatio_expandY (self):
        self.analyzer.expand_perc = 0
        self.analyzer.ratio = 1/1
        roi = [3, 3, 4, 6]
        result = self.analyzer.expandRoiToRatio(roi, (10, 20))
        self.assertEqual (result, [2, 3, 5, 6])

    def test_expandRoiToRatio_expandX (self):
        self.analyzer.expand_perc = 0
        self.analyzer.ratio = 1/1
        roi = [3, 3, 6, 4]
        result = self.analyzer.expandRoiToRatio(roi, (10, 20))
        self.assertEqual (result, [3, 2, 6, 5])

    def test_expandRoiToRatio_ratioKillsExpand (self):
        self.analyzer.expand_perc = 1
        self.analyzer.ratio = 1/1
        roi = [3, 3, 4, 8]
        result = self.analyzer.expandRoiToRatio(roi, (10, 20))
        self.assertEqual (result, [1, 3, 6, 8])

    def test_expandRoiToRatio_ratioAndExpand (self):
        self.analyzer.expand_perc = 1
        self.analyzer.ratio = 1/1
        roi = [1, 18, 8, 20]
        result = self.analyzer.expandRoiToRatio(roi, (10, 20))
        self.assertEqual (result, [1, 12, 8, 19]);



if __name__ == '__main__':
    logging.basicConfig (level=logging.CRITICAL)
    unittest.main()
