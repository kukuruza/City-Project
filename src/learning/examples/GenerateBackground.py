#! /usr/bin/env python
import os, sys, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup import setupLogging, dbInit
from learning.dbModify import generateBackground


setupLogging ('log/learning/GenerateBackground.log', logging.INFO, 'a')

parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--out_db_file', required=True)
parser.add_argument('--out_videofile', required=True)
parser.add_argument('--logging_level', default=20, type=int)
parser.add_argument('--dilate_radius', default=2, type=int)
args = parser.parse_args()

setupLogging ('log/learning/GenerateBackground.log', args.logging_level, 'a')

(conn, cursor) = dbInit(args.in_db_file, args.out_db_file)
generateBackground (cursor, args.out_videofile, 
                    params={'show_debug': False, 
                            'dilate_radius': args.dilate_radius})
conn.commit()
conn.close()


