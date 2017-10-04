#! /usr/bin/env python2
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup import setupLogging, dbInit
from learning.synth2real.dbNpz import dbExportCarsNpz
from learning.dbModify import filterCustom, expandBboxes, filterByBorder


parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--logging_level', default=20, type=int)
args, _ = parser.parse_known_args()

setupLogging ('log/learning/synth2real/ExportNpz.log', args.logging_level, 'a')

(conn, cursor) = dbInit(args.in_db_file, backup=False)
filterCustom(cursor, sys.argv[1:])
filterByBorder(cursor, sys.argv[1:])
expandBboxes(cursor, sys.argv[1:])
dbExportCarsNpz(cursor, sys.argv[1:])
conn.close()

