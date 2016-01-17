'''Run blender for each video frame separately'''

import sys, os, os.path as op
import glob
import subprocess
import re
import shutil
import logging
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
from helperSetup import setupLogging

setupLogging('log/augmentation/renderScene.log', logging.DEBUG, 'a')

scene_path        = op.join(os.getenv('CITY_DATA_PATH'), 'augmentation/scenes/cam572-Jan13-10h.blend')
render_dir        = op.join(os.getenv('CITY_DATA_PATH'), 'augmentation/render/try02')
traffic_template  = op.join(os.getenv('CITY_DATA_PATH'), 'augmentation/traffic/try02/traffic-fr*.json')

render_work_dir   = op.join(os.getenv('CITY_DATA_PATH'), 'augmentation/render/current-frame')
traffic_work_path = op.join(os.getenv('CITY_DATA_PATH'), 'augmentation/traffic/current-frame.json')


blender_path = '/Applications/blender.app/Contents/MacOS/blender'

for i_frame,traffic_frame in enumerate(glob.glob(traffic_template)):

    # copy frame json to file to traffic-current.json
    logging.info ('traffic_frame: %s' % traffic_frame)
    traffic_dirname = op.dirname(traffic_frame)
    shutil.copyfile (traffic_frame, traffic_work_path)

    command = '%s %s --background --python %s/src/augmentation/renderScene.py' % \
              (blender_path, scene_path, os.getenv('CITY_PATH'))
    returncode = subprocess.call ([command], shell=True)
    logging.info ('blender returned code %s' % str(returncode))

    # give the rendered dir a unique name 
    render_frame_dir = op.join(render_dir, 'fr%06d' % i_frame)
    logging.debug ('render dir %s from traffic file %s' % (render_frame_dir, traffic_frame))
    if op.exists(render_frame_dir):
        shutil.rmtree(render_frame_dir)
    shutil.move (render_work_dir, render_frame_dir)
