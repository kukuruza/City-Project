'''Run blender for each video frame separately'''

import sys, os, os.path as op
import glob
import subprocess
import re
import shutil

traffic_template = op.join(os.getenv('CITY_DATA_PATH'), 'augmentation/traffic/traffic-fr*.json')
render_dir       = op.join(os.getenv('CITY_DATA_PATH'), 'augmentation/render')
render_current_dir = op.join(render_dir, 'current-frame')

blender_path = '/Applications/blender.app/Contents/MacOS/blender'

for traffic_frame in glob.glob(traffic_template):

    # copy frame json to file to traffic-current.json
    traffic_dirname = op.dirname(traffic_frame)
    shutil.copyfile (traffic_frame, op.join(traffic_dirname, 'traffic-current-frame.json'))

    command = '%s --background --python %s/src/augmentation/renderScene.py' % \
              (blender_path, os.getenv('CITY_PATH'))
    returncode = subprocess.call ([command], shell=True)

    # give the rendered dir a unique name 
    name = op.basename (traffic_frame)
    i_frame = re.findall (r'\d+', traffic_frame)[0]
    render_frame_dir = op.join(render_dir, 'fr-%s' % i_frame)
    print render_frame_dir
    if op.exists(render_frame_dir):
        shutil.rmtree(render_frame_dir)
    shutil.move (render_current_dir, render_frame_dir)

