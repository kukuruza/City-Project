#! /usr/bin/env python
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup import setupLogging, dbInit
from learning.dbModify import filterCustom, expandBboxes, filterByBorder, thresholdScore


parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--out_db_file', required=True)
parser.add_argument('--logging_level', default=20, type=int)
parser.add_argument('--image_constraint', required=False,
        help='''e.g.: 'substr(imagefile, -5) < "04500" OR substr(imagefile, -5) >= "09000"' ''',
        default='1')
parser.add_argument('--car_constraint', required=False,
        help='''e.g.: 'width >= 25' ''',
        default='1')
parser.add_argument('--filter_by_border', action='store_true')
parser.add_argument('--expand_bboxes_02', action='store_true')  # temporary
args = parser.parse_args()

setupLogging ('log/learning/Filter.log', args.logging_level, 'a')


(conn, cursor) = dbInit (args.in_db_file, args.out_db_file)
if args.filter_by_border:
    filterByBorder (cursor)
    thresholdScore (cursor)
filterCustom (cursor, params={'car_constraint': args.car_constraint, 'image_constraint': args.image_constraint})
if args.expand_bboxes_02:  # temporary
    expandBboxes (cursor, params={'expand_perc': 0.2, 'keep_ratio': False})
conn.commit()
conn.close()

