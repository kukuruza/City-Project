#! /usr/bin/env python
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup import setupLogging, atcity, dbInit
from learning.dataset2video import dataset2video


parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True,
        help='data/augmentation/video/cam572/Feb23-09h-Dec01/init-back.db')
parser.add_argument('--out_video_file', required=True,
        help='data/augmentation/video/cam572/Feb23-09h-Dec01/back.avi')
parser.add_argument('--logging_level', default=20, type=int)
setupLogging ('log/learning/Dataset2Video.log', logging.INFO, 'a')

(conn, cursor) = dbInit (in_db_file)
dataset2video(cursor, out_image_video_file=out_video_file)
conn.close()

