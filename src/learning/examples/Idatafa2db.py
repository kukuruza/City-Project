#! /usr/bin/env python
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup         import setupLogging, dbInit
from learning.labelme.idatafa2db  import parseIdatafaFolder
 

parser = argparse.ArgumentParser()
parser.add_argument('--in_video_file', required=True,
                    help='E.g. data/camdata/170/170-20160425-18.avi')
parser.add_argument('--out_db_file', required=True,
                    help='E.g. databases/170-20160425-18/parsed.db')
parser.add_argument('--logging_level', default=20, type=int)
parser.add_argument('--debug_show', action='store_true')
args = parser.parse_args()

setupLogging ('log/learning/Idatafa2db.log', args.logging_level, 'a')

parseIdatafaFolder (args.in_video_file, args.out_db_file, 
  params={'debug_show': args.debug_show})

