import os, sys, os.path as op
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning/annotations'))
import random
import unittest

from terms import TermTree
import json
import logging



class TestTerms (unittest.TestCase):

    dictionary_path = op.join(os.getenv('CITY_PATH'), 'src/learning/annotations/dictionary.json')

    def setUp(self):
        json_file = open(self.dictionary_path);
        self.terms = TermTree.from_dict(json.load(json_file))
        json_file.close()

    def test_top(self):
        self.assertEqual(self.terms.best_match('object'), 'object')

    def test_exact(self):
        self.assertEqual(self.terms.best_match('car'), 'sedan')

    def test_propagate(self):
        self.assertEqual(self.terms.best_match('sedan'), 'sedan')
        self.assertEqual(self.terms.best_match('bicycle'), 'object')

    def test_notfound(self):
        self.assertEqual(self.terms.best_match('hahaha'), 'object')

    def test_get_path_to_node_ (self):
        self.assertEqual(self.terms._get_path_to_node_('object'), ['object'])
        self.assertEqual(self.terms._get_path_to_node_('sedan'), ['object', 'vehicle', 'sedan'])
        self.assertIsNone(self.terms._get_path_to_node_('hahaha'))

    def test_get_common_root (self):
        self.assertEqual (self.terms.get_common_root('bus', 'van'), 'vehicle')
        self.assertEqual (self.terms.get_common_root('car', 'sedan'), 'sedan')
        self.assertEqual (self.terms.get_common_root('sedan', 'car'), 'sedan')
        self.assertEqual (self.terms.get_common_root('example', 'car'), 'object')
        with self.assertRaises (Exception): self.terms.get_common_root('car', 'hahaha')


if __name__ == '__main__':
    logging.basicConfig (level=logging.CRITICAL)
    unittest.main()
