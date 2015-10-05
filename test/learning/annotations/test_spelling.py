import os, sys, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning/annotations'))
import random
import unittest
import logging

from spelling import SpellingCorrector


class TestSpellCorrector (unittest.TestCase):

    dictionary_path = op.join(os.getenv('CITY_PATH'), 'src/learning/annotations/dictionary.json')

    def setUp(self):
        self.corrector = SpellingCorrector()
        self.corrector.train(self.dictionary_path);

    def test_correct_word(self):
        self.assertEqual(self.corrector.correct('spelling'), 'spelling',
            'Wrong answer in a correct word "spelling"')

    def test_incorrect_word(self):
        self.assertEqual(self.corrector.correct('speling'), 'spelling',
            'Wrong answer in a incorrect word "speling"')

if __name__ == '__main__':
    logging.basicConfig (level=logging.CRITICAL)
    unittest.main()
