#! /usr/bin/env python
import os, sys, os.path as op
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from glob import glob
from learning.helperSetup         import setupLogging, dbInit, atcity
from learning.labelme.idatafa2db  import parseIdatafaFolder
 

parser = argparse.ArgumentParser()
parser.add_argument('--in_video_template', required=True,
                    help='E.g. data/camdata/170/*.avi')
parser.add_argument('--logging_level', default=20, type=int)
parser.add_argument('--debug_show', action='store_true')
parser.add_argument('--bboxes_video', action='store_true')
args = parser.parse_args()

setupLogging ('log/learning/Idatafa2dbMulti.log', args.logging_level, 'a')

for in_video_path in sorted(glob(atcity(args.in_video_template))):
  print ('in_video_path: %s' % in_video_path)
  if 'parsed' in in_video_path:
    logging.info('skipping %s which is not src video' % in_video_path)
    continue
  videoname = op.basename(op.splitext(in_video_path)[0])
  out_db_file = op.join('data/databases/idatafa', videoname, 'parsed.db')
  logging.info ('out_db_file: %s' % out_db_file)
  parseIdatafaFolder (in_video_path, out_db_file, 
    params={'debug_show': args.debug_show,
            'bboxes_video': args.bboxes_video})

