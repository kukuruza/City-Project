import logging
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/backend'))
import helperSetup
import video2dataset

helperSetup.setupLogging ('log/learning/Video2Dataset.log', logging.INFO, 'a')

videos_prefix = 'camdata/cam671/Jul28-17h'
db_prefix = 'databases/test/671-Jul28-17h'

video2dataset.makeDataset (videos_prefix, db_prefix)
