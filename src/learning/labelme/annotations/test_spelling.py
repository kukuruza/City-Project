import random
import unittest
import logging

from spelling import SpellingCorrector


class TestSpellCorrector (unittest.TestCase):

    def setUp(self):
        self.corrector = SpellingCorrector()
        self.corrector.train('dictionary.json');

    def test_correct_word(self):
        self.assertEqual(self.corrector.correct('spelling'), 'spelling',
            'Wrong answer in a correct word "spelling"')

    def test_incorrect_word(self):
        self.assertEqual(self.corrector.correct('speling'), 'spelling',
            'Wrong answer in a incorrect word "speling"')

if __name__ == '__main__':
    logging.basicConfig (level=logging.CRITICAL)
    unittest.main()
