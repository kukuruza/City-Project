#! /usr/bin/env python
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup import setupLogging, dbInit
from learning.dbModify    import merge, expandBboxes, filterByBorder


parser = argparse.ArgumentParser()
parser.add_argument('--in_db_files', nargs='+', required=True)
parser.add_argument('--out_db_file', required=True)
parser.add_argument('--logging_level', default=20, type=int)
args = parser.parse_args()

setupLogging ('log/learning/Merge.log', args.logging_level, 'a')


(conn1, cursor1) = dbInit(args.in_db_files[0], args.out_db_file)

for in_db_file in args.in_db_files[1:]:
  (conn2, cursor2) = dbInit(in_db_file, backup=False)
  merge(cursor1, cursor2)
  conn2.close()

conn1.commit()
conn1.close()



