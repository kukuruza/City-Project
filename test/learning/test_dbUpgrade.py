import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
import random
import logging
import sqlite3
import unittest
import helperTesting
from helperDb import doesTableExist, isColumnInTable
from dbUpgrade import *




if __name__ == '__main__':
    logging.basicConfig (level=logging.ERROR)
    unittest.main()
