#! /usr/bin/env python
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup import setupLogging, dbInit, ArgumentParser
from learning.dbManual import display
from learning.dbModify import filter


parser = ArgumentParser('Display')
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--logging_level', default=20, type=int)
args, _ = parser.parse_known_args()
argv = sys.argv[1:]

setupLogging ('log/learning/Display.log', args.logging_level, 'a')

(conn, cursor) = dbInit(args.in_db_file, backup=False)
try: filter (cursor, argv)
except: pass
display (cursor, argv)
conn.close()

