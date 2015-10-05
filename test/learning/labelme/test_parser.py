import os, sys, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning/labelme'))
import random
import unittest
import logging

import parser
#from parser import BaseParser, FrameParser, PairParser


class TestBaseParser (unittest.TestCase):

    def setUp(self):
        self.parser = parser.BaseParser ()

    def test_none(self):
        phrase = ' :)  :-(  ;-*';
        self.assertEqual (self.parser.to_bag_of_words (phrase), [],
            'Returned non-empty list on phrase: ' + phrase)

    def test_one_word(self):
        phrase = '>>> vam ';
        answer = ['van'];
        self.assertEqual (self.parser.to_bag_of_words (phrase), answer,
            'Wrong answer on phrase: ' + phrase)

    def test_many_words(self):
        phrase = '555 6 \%~~--: =%^ ';
        answers = set({'555', '6'});
        self.assertTrue (self.parser.to_bag_of_words (phrase))
        self.assertEqual (set(self.parser.to_bag_of_words (phrase)), answers,
            'Wrong answer on phrase: ' + phrase)

        phrase = 'LazyLinna   sleeps 10hours!!!!!11 ';
        answers = set({'object', 'object', '10', 'object', '11'});
        self.assertTrue (self.parser.to_bag_of_words (phrase))
        self.assertEqual (set(self.parser.to_bag_of_words (phrase)), answers,
            'Wrong answer on phrase: ' + phrase)



class TestFrameParser (unittest.TestCase):

    def setUp(self):
        self.parser = parser.FrameParser()

    def test_none(self):
        phrase = '555 6 \%~~--: =%^ ';
        self.assertFalse (self.parser.parse (phrase),
            'Gave some answer when should be None on: ' + phrase)

    def test_one_word(self):
        phrase = 'LazyLinna   sleeps 10hours !!!!!11 ';
        self.assertEqual (self.parser.parse (phrase), 'object',
            'Wrong answer on phrase: ' + phrase)

        phrase = 'black vam ';
        self.assertEqual (self.parser.parse (phrase), 'van',
            'Wrong answer on phrase: ' + phrase)

    def test_many_words(self):
        phrase = 'LazyLinna   sleeps 10hours in any bus or car !!!!!11 ';
        self.assertFalse (self.parser.parse(phrase), 
            'Gave some answer when should be None on: ' + phrase)



class TestPairParser (unittest.TestCase):

    def setUp(self):
        self.parser = parser.PairParser()

    def test_none(self):
        phrase = 'too many cars (car-s)';
        (name, number) = self.parser.parse (phrase)
        self.assertTrue ((name, number) == (None, None),
            'Gave some answer when should be None on: ' + phrase)

        phrase = 'LazyLinna   sleeps 10hours !!!!!11111 ';
        (name, number) = self.parser.parse (phrase)
        self.assertTrue ((name, number) == (None, None),
            'Gave some answer when should be None on: ' + phrase)


    def test_word_only (self):
        phrase = 'LazyLinna   sleeps hours !!!!! ';
        (name, number) = self.parser.parse (phrase)
        self.assertTrue (type(name) == str)
        self.assertTrue (name is not None and number is not None)
        self.assertTrue (name ==  'object' and number > 100,
            'Answered (' + name + ', ' + str(number) + ') on phrase: ' + phrase)


    def test_number_only (self):
        phrase = '4';
        (name, number) = self.parser.parse (phrase)
        self.assertTrue (type(name) == str)
        self.assertTrue ((name, number) == ('sedan', 4),
            'Answered (' + name + ', ' + str(number) + ') on phrase: ' + phrase)

        phrase = '>>> 0  ';
        (name, number) = self.parser.parse (phrase)
        self.assertTrue (type(name) == str)
        self.assertTrue ((name, number) == ('sedan', 0),
            'Answered (' + name + ', ' + str(number) + ') on phrase: ' + phrase)


    def test_word_and_number (self):
        phrase = 'black cart 4 ';
        (name, number) = self.parser.parse (phrase)
        self.assertTrue (type(name) == str)
        self.assertTrue ((name, number) == ('sedan', 4),
            'Answered (' + name + ', ' + str(number) + ') on phrase: ' + phrase)

        phrase = '>>> 0 object  ';
        (name, number) = self.parser.parse (phrase)
        self.assertTrue (type(name) == str)
        self.assertTrue ((name, number) == ('object', 0),
            'Answered (' + name + ', ' + str(number) + ') on phrase: ' + phrase)





if __name__ == '__main__':
    logging.basicConfig (level=logging.CRITICAL)
    unittest.main()



