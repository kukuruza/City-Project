import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
from learning.dataset2video import dataset2video
from learning.helperSetup import setupLogging, atcity, dbInit


setupLogging ('log/learning/Dataset2Video.log', logging.INFO, 'a')

in_db_file = 'augmentation/video/cam572/Feb23-09h-Dec01/init-[--]-back.db'
out_video_file = 'augmentation/video/cam572/Feb23-09h-Dec01/back.avi'

(conn, cursor) = dbInit (in_db_file)
dataset2video(cursor, out_image_video_file=out_video_file)
conn.close()
