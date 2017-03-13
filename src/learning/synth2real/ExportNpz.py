#! /usr/bin/env python2
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup import setupLogging, dbInit
from learning.synth2real.dbNpz import dbExportCarsNpz


parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--out_file', required=True, type=str)
parser.add_argument('--width', required=True, type=int)
parser.add_argument('--height', required=True, type=int)
parser.add_argument('--grayscale', action='store_true')
parser.add_argument('--logging_level', default=20, type=int)
args = parser.parse_args()

setupLogging ('log/learning/synth2real/ExportNpz.log', args.logging_level, 'a')

(conn, cursor) = dbInit(args.in_db_file, backup=False)
dbExportCarsNpz(cursor, args.out_file, params={'grayscale': args.grayscale, 'width': args.width, 'height': args.height})
conn.close()

