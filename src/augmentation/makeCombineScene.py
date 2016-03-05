import bpy
import os, os.path as op
import sys
import json
import logging
from mathutils import Color, Euler, Vector
from learning.helperSetup import atcity

import numpy as np

WORK_COMBINE_DIR = atcity('augmentation/blender/current-scene')
SCENES_INFO_NAME = 'scene.json'


def dump(obj):
   '''Helper function to output all properties of an object'''
   for attr in dir(obj):
       if hasattr( obj, attr ):
           print( "obj.%s = %s" % (attr, getattr(obj, attr)))


def hsv_correction (video_info):
    hsv_node = bpy.context.scene.node_tree.nodes['Hue-Saturation-Compensation']
    if 'blender_hsv' in video_info:
        blender_hsv = video_info['blender_hsv']
        if 'h' in blender_hsv: hsv_node.color_hue        = blender_hsv['h']
        if 's' in blender_hsv: hsv_node.color_saturation = blender_hsv['s']
        if 'v' in blender_hsv: hsv_node.color_value      = blender_hsv['v']
    else:
        logging.warning ('combine_scene: no blender_hsv information in video_info')


def camera_blur (camera_info):
    blur_node = bpy.context.scene.node_tree.nodes['Camera-Blur']
    if 'blender_blur' in camera_info:
        blender_blur = camera_info['blender_blur']
        if 'X'    in blender_blur: blur_node.center_x = blender_blur['X']
        if 'Y'    in blender_blur: blur_node.center_y = blender_blur['Y']
        if 'zoom' in blender_blur: blur_node.zoom     = blender_blur['zoom']


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
    frame_name = '//%s' % video_info['example_frame_name']
    bpy.data.images['frame-1.png'].filepath = frame_name

    hsv_correction (video_info)

    camera_blur (camera_info)

    assert op.exists(op.dirname(out_path)), 'out_path: %s' % out_path
    bpy.ops.wm.save_as_mainfile (filepath=out_path)



scene_info = json.load(open( op.join(WORK_COMBINE_DIR, SCENES_INFO_NAME) ))

default_combine_scene (scene_info)

