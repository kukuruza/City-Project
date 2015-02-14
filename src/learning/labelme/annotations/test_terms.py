import random
import unittest

from terms import TermTree
import json
import logging



class TestTerms (unittest.TestCase):

    def setUp(self):
        json_file = open('dictionary.json');
        self.terms = TermTree.from_dict(json.load(json_file))
        json_file.close()

    def test_top(self):
        self.assertEqual(self.terms.best_match('object'), 'object',
            'Wrong answer on word "object"')

    def test_exact(self):
        self.assertEqual(self.terms.best_match('car'), 'car',
            'Wrong answer on word "car"')

    def test_propagate(self):
        self.assertEqual(self.terms.best_match('sedan'), 'car',
            'Wrong answer on word "sedan"')
        self.assertEqual(self.terms.best_match('bicycle'), 'object',
            'Wrong answer on word "bicycle"')

    def test_notfound(self):
        self.assertEqual(self.terms.best_match('hahaha'), 'object',
            'Wrong answer on word "hahaha"')

if __name__ == '__main__':
    logging.basicConfig (level=logging.CRITICAL)
    unittest.main()
