import logging
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
import helperSetup
import video2dataset

helperSetup.setupLogging ('log/learning/Video2Dataset.log', logging.INFO, 'a')

videos_prefix = 'camdata/cam671/Jul28-17h'
dataset_dir = 'datasets/test'
dataset_name = '671-Jul28-17h'

video2dataset.makeDataset (videos_prefix, dataset_dir, dataset_name)
