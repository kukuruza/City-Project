import random
import unittest

import logging
from dbInterface import parseFilterName, queryCars, directQuery


class Test_dbInterface (unittest.TestCase):

    def setUp(self):
        self.db_path = 'testdata/test-frames.db'

    def test_parseFilterName (self):
        self.assertEqual (parseFilterName('width.min'), ('width', '>='))
        self.assertEqual (parseFilterName('width.max'), ('width', '<='))
        self.assertEqual (parseFilterName('width.equal'), ('width', '='))
        self.assertEqual (parseFilterName('width'), ('width', '='))
        self.assertRaises (Exception, parseFilterName, 'width.ahaha')
        self.assertRaises (Exception, parseFilterName, 'width.min.max')

    def test_directQuery (self):
        response = directQuery (self.db_path, 'SELECT name FROM cars WHERE name="van"')
        self.assertEqual (type(response), list)
        self.assertEqual (len(response), 1)
        self.assertEqual (type(response[0]), tuple)
        self.assertEqual (response[0][0], 'van')    # note, 2nd index is 0

    def test_queryCars_one (self):
        response = queryCars (self.db_path, { 'filter': 'van_only', 'name': 'van' })
        #print (response)
        self.assertEqual (type(response), list)
        self.assertEqual (len(response), 1)
        self.assertEqual (type(response[0]), tuple)
        self.assertEqual (len(response[0]), 11)
        self.assertEqual (response[0][2], 'van')

    def test_queryCars_many (self):
        response = queryCars (self.db_path, { 'name': 'car', 'width.min': '83' })
        #print (response)
        self.assertEqual (type(response), list)
        self.assertEqual (len(response), 2)
        self.assertEqual (type(response[0]), tuple)
        self.assertEqual (response[0][2], 'car')

    def test_queryCars_3fields (self):
        filters = { 'filter': 'van_only', 'name': 'van' }
        fields = ['height', 'name', 'yaw']
        response = queryCars (self.db_path, filters, fields)
        #print (response)
        self.assertEqual (type(response), list)
        self.assertEqual (len(response), 1)
        self.assertEqual (type(response[0]), tuple)
        self.assertEqual (len(response[0]), 3)
        self.assertEqual (response[0][1], 'van')




if __name__ == '__main__':
    logging.basicConfig (level=logging.CRITICAL)
    unittest.main()

