#! /usr/bin/env python
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup import setupLogging, dbInit
from learning.dbModify import filter, expandBboxes


parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--out_db_file', required=True)
parser.add_argument('--logging_level', default=20, type=int)
parser.add_argument('--expand_bboxes', action='store_true')
args, _ = parser.parse_known_args()
argv = sys.argv[1:]

setupLogging ('log/learning/Filter.log', args.logging_level, 'a')


(conn, cursor) = dbInit (args.in_db_file, args.out_db_file)
filter (cursor, argv)
if args.expand_bboxes:
  expandBboxes (cursor, argv)
conn.commit()
conn.close()

