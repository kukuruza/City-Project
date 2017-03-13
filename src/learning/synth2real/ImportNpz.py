#! /usr/bin/env python2
import os, sys, os.path as op
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup import setupLogging, dbInit
from dbNpz import dbReplaceCarsWithNpz


parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--in_npz_file', required=True, type=str)
parser.add_argument('--out_db_file', required=True)
parser.add_argument('--num', default=1000000000000, type=int)
parser.add_argument('--car_constraint', default='1')
parser.add_argument('--image_constraint', default='1')
parser.add_argument('--logging_level', default=20, type=int)
args = parser.parse_args()

setupLogging ('log/learning/synth2real/ImportNpz.log', args.logging_level, 'a')

out_video_file = op.join(op.relpath(op.dirname(args.out_db_file), os.getenv('CITY_DATA_PATH')), 'image.avi')

(conn, cursor) = dbInit(args.in_db_file, args.out_db_file)
dbReplaceCarsWithNpz(cursor, args.in_npz_file, out_video_file, 
        params={'num': args.num, 'image_constraint': args.image_constraint, 
            'car_constraint': args.car_constraint})
conn.commit()
conn.close()

