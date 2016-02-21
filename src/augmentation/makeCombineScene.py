import bpy
import os, os.path as op
import sys
import json
import logging
from mathutils import Color, Euler, Vector
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
from helperSetup import atcity

WORK_DIR         = atcity('augmentation/blender/current-scene')
SCENES_INFO_NAME = 'scene.json'


def default_combine_scene (scene_info):
    '''Right now, just change the image resolution
    '''
    in_path  = atcity(scene_info['in_combine_file'])
    out_path = atcity(scene_info['out_combine_file'])
    camera_info = scene_info['camera_info']

    bpy.ops.wm.open_mainfile (filepath=atcity(in_path))

    # set camera resolution
    bpy.context.scene.render.resolution_x = camera_info['camera_dims']['width']
    bpy.context.scene.render.resolution_y = camera_info['camera_dims']['height']

    assert op.exists(op.dirname(out_path)), 'out_path: %s' % out_path
    bpy.ops.wm.save_as_mainfile (filepath=out_path)




scene_info = json.load(open( op.join(WORK_DIR, SCENES_INFO_NAME) ))

default_combine_scene (scene_info)

