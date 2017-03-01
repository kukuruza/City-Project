#! /usr/bin/env python
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup import setupLogging, dbInit
from learning.dbModify    import splitToRandomSets


parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--out_db_file', required=True)
parser.add_argument('--logging_level', default=20, type=int)

setupLogging ('log/learning/Split.log', args.logging_level, 'a')

(conn, cursor) = dbInit(in_db_file)
db_out_names = {'test2': 0.005}
splitToRandomSets (cursor, os.path.dirname(args.in_db_file), db_out_names)
conn.close()
