#! /usr/bin/env python
import os, sys, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup import setupLogging, dbInit
from learning.dbModify import keepFraction


parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--out_db_file', required=True)
parser.add_argument('--keep_fraction', required=True, type=float)
parser.add_argument('--randomly', action='store_true')
parser.add_argument('--logging_level', default=20, type=int)
args = parser.parse_args()

setupLogging ('log/learning/KeepFraction.log', args.logging_level, 'a')


(conn, cursor) = dbInit (args.in_db_file, args.out_db_file)
keepFraction(cursor, keep_fraction=args.keep_fraction, randomly=args.randomly)
conn.commit()
conn.close()

