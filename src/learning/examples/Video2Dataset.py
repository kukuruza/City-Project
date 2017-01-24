import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
from learning.helperSetup import setupLogging
from learning.video2dataset import make_dataset

setupLogging ('log/learning/Video2Dataset.log', logging.INFO, 'a')

video_dir = 'camdata/cam164/Feb23-09h'
db_file   = 'databases/idatafa/164-Feb23-09h/init-allimages.db'
make_dataset(video_dir, db_file)
