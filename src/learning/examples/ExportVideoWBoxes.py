#! /usr/bin/env python
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup import setupLogging, dbInit
from learning.dataset2imagery import exportVideoWBoxes


parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--out_videofile', required=True)
parser.add_argument('--logging_level', default=20, type=int)
args = parser.parse_args()

setupLogging ('log/learning/ExportVideoWBoxes.log', args.logging_level, 'a')

(conn, cursor) = dbInit(args.in_db_file, backup=False)
exportVideoWBoxes(cursor, args.out_videofile, params={})
conn.close()

