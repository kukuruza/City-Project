#! /usr/bin/env python
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup import setupLogging, dbInit
from learning.dbModify    import moveDir


parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--out_db_file', required=True)
parser.add_argument('--images_dir', required=False)
parser.add_argument('--masks_dir', required=False)

parser.add_argument('--logging_level', default=20, type=int)
args = parser.parse_args()

setupLogging ('log/learning/MoveDir.log', args.logging_level, 'a')

(conn, cursor) = dbInit(args.in_db_file, args.out_db_file)
moveDir (cursor, params={'images_dir': args.images_dir, 'masks_dir': args.masks_dir})

conn.commit()
conn.close()

