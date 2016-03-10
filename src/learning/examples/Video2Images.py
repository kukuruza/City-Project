import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
from learning.video2images import video2images
from learning.helperSetup import setupLogging, atcity


setupLogging ('log/learning/Video2Images.log', logging.INFO, 'a')

video2images('camdata/cam166/Feb14-08h/src.avi',
             'labelme/try')
