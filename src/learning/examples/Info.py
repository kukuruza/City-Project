#! /usr/bin/env python
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from pprint import pprint
from learning.helperSetup import setupLogging, dbInit
from learning.dbManual import getInfo
from learning.dbModify import filterCustom


parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--logging_level', default=20, type=int)
args, _ = parser.parse_known_args()

setupLogging ('log/learning/Info.log', args.logging_level, 'a')

(conn, cursor) = dbInit(args.in_db_file, backup=False)
filterCustom(cursor, sys.argv[1:])
info = getInfo(cursor, sys.argv[1:])
pprint (info, width=120)
conn.close()

