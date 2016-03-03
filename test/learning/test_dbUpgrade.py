import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import random
import logging
import sqlite3
import unittest
from helperTesting       import TestMicroDbBase
from learning.helperDb  import doesTableExist, isColumnInTable
from learning.dbUpgrade import *




if __name__ == '__main__':
    logging.basicConfig (level=logging.ERROR)
    unittest.main()
