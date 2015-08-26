import os, sys
sys.path.insert(0, os.path.abspath('..'))
import random
import logging
import sqlite3
import unittest
import helperTesting
from helperDb import checkTableExists, isColumnInTable
from dbUpgrade import *




if __name__ == '__main__':
    logging.basicConfig (level=logging.ERROR)
    unittest.main()
