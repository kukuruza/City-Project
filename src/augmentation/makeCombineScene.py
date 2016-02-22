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


def dump(obj):
   '''Helper function to output all properties of an object'''
   for attr in dir(obj):
       if hasattr( obj, attr ):
           print( "obj.%s = %s" % (attr, getattr(obj, attr)))


def default_combine_scene (scene_info):
    '''Right now, just change the image resolution
    '''
    in_path  = atcity(scene_info['in_combine_file'])
    out_path = atcity(scene_info['out_combine_file'])
    camera_info = scene_info['camera_info']
    video_info  = scene_info['video_info']

    bpy.ops.wm.open_mainfile (filepath=atcity(in_path))

    width  = camera_info['camera_dims']['width']
    height = camera_info['camera_dims']['height']

    # set camera resolution
    bpy.context.scene.render.resolution_x = width
    bpy.context.scene.render.resolution_y = height

    # change the image to the proper one
    # change the file directory
    bpy.ops.wm.save_as_mainfile (filepath=out_path)
    bpy.ops.wm.open_mainfile (filepath=out_path)
    # change the file name
    frame_path = '//%s' % video_info['example_frame_name']
    bpy.data.images['frame-1.png'].filepath = frame_path

    assert op.exists(op.dirname(out_path)), 'out_path: %s' % out_path
    bpy.ops.wm.save_as_mainfile (filepath=out_path)



scene_info = json.load(open( op.join(WORK_DIR, SCENES_INFO_NAME) ))

default_combine_scene (scene_info)

