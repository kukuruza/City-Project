#! /usr/bin/env python
import os, sys, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup import setupLogging, dbInit
from learning.dbModify import expandBboxes


parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--out_db_file', required=True)
parser.add_argument('--expand_perc', default=0.2, type=float)
parser.add_argument('--logging_level', default=20, type=int)
args = parser.parse_args()

setupLogging ('log/learning/ExpandBBoxes.log', args.logging_level, 'a')


(conn, cursor) = dbInit (args.in_db_file, args.out_db_file)
expandBboxes (cursor, params={'expand_perc': args.expand_perc, 'keep_ratio': False})
conn.commit()
conn.close()

