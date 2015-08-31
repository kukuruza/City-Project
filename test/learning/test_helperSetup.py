import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
import random
import logging
import sqlite3
import unittest
import helperTesting
from helperSetup import *
from helperSetup import _setupCopyDb_


class TestParams (unittest.TestCase):
    ''' processing of passes 'params' argument '''

    def test_assertParamIsThere_yes (self):
        with self.assertRaises(Exception):
            assertParamIsThere({'dummy': 'dummyValue'}, 'checkMe')

    def test_assertParamIsThere_no (self):
        assertParamIsThere({'dummy': 'dummyValue'}, 'dummy')

    def test_setParamUnlessThere_exists (self):
        params = {'dummy': 'dummyValue'}
        setParamUnlessThere (params, 'dummy', 'defaultValue')
        self.assertTrue ('dummy' in params)
        self.assertEqual (params['dummy'], 'dummyValue')

    def test_setParamUnlessThere_default (self):
        params = {}
        setParamUnlessThere (params, 'dummy', 'defaultValue')
        self.assertTrue ('dummy' in params)
        self.assertEqual (params['dummy'], 'defaultValue')


class TestSetupCopyDb (unittest.TestCase):
    ''' test the helper _setupCopyDb_ function '''

    def setUp(self):
        # create dummy files
        open('in', 'w').close()
        open('out', 'w').close()

    def test_checkDbExists (self):
        with self.assertRaises(Exception):
            _setupCopyDb_ ('dummy')

    def test_normal (self):
        _setupCopyDb_ ('in', 'out_2')
        self.assertTrue (op.exists('out_2'))

    def test_sameInOut (self):
        _setupCopyDb_ ('in', 'in')
        self.assertTrue (op.exists('in.backup'))

    def test_backUpOut (self):
        _setupCopyDb_ ('in', 'out')
        self.assertTrue (op.exists('out.backup'))

    def tearDown(self):
        for path in ['in', 'in.backup', 'out', 'out.backup', 'out_2']:
            if op.exists(path): os.remove(path)


class TestInit (unittest.TestCase):
    ''' test the whole pipeline to open files '''

    def setUp(self):
        self.in_path  = op.join(os.getenv('CITY_DATA_PATH'), 'in.db')
        self.out_path = op.join(os.getenv('CITY_DATA_PATH'), 'out.db')
        conn = sqlite3.connect (self.in_path)
        conn.commit()
        conn.close()

    def tearDown(self):
        for path in ['in.db', 'out.db', 'out.db.backup']:
            path = op.join(os.getenv('CITY_DATA_PATH'), path)
            if op.exists(path): os.remove(path)

    def test_nothing (self):
        dbInit (self.in_path, self.out_path)

    def test_returnValid (self):
        (conn, cursor) = dbInit (self.in_path, self.out_path)
        cursor.execute ('SELECT "Hello world"')
        conn.commit()
        conn.close()


if __name__ == '__main__':
    logging.basicConfig (level=logging.ERROR)
    unittest.main()
