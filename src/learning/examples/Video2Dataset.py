import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup import setupLogging, dbInit
from learning.video2dataset import make_dataset


parser = argparse.ArgumentParser()
parser.add_argument('--out_db_file', required=True)
parser.add_argument('--in_video_dir', required=True)
parser.add_argument('--logging_level', default=20, type=int)
args = parser.parse_args()

setupLogging ('log/learning/Video2Dataset.log', args.logging_level, 'a')

make_dataset(args.in_video_dir, args.out_db_file)

