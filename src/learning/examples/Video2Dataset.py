import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
from learning.helperSetup import setupLogging
from learning.video2dataset import makeDataset, make_back_dataset

setupLogging ('log/learning/Video2Dataset.log', logging.INFO, 'a')

#videos_prefix = 'camdata/cam572/Jan13-10h-shadows'
#db_prefix = 'databases/augmentation/671-Jan13-10h'
#video2dataset.makeDataset (videos_prefix, db_prefix)

video_dir = 'camdata/cam717/Apr07-15h'
db_file   = 'databases/augmentation/Apr07-15h-back.db'
make_back_dataset(video_dir, db_file)
