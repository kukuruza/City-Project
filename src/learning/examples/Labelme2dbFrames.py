#! /usr/bin/env python
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup         import setupLogging, dbInit
from learning.labelme.labelme2db  import folder2frames
 

parser = argparse.ArgumentParser()
parser.add_argument('--in_annotations_dir', required=True)
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--out_db_file', required=True)
parser.add_argument('--logging_level', default=20, type=int)
args = parser.parse_args()

setupLogging ('log/learning/Labelme2dbFrames.log', args.logging_level, 'a')

(conn, cursor) = dbInit(db_in_file, db_out_file)
folder2frames (cursor, in_annotations_dir, params={})
conn.commit()
conn.close()
