import bpy
import os, os.path as op
import sys
import json
import logging
from mathutils import Color, Euler, Vector
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/augmentation'))
from helperSetup import atcity

WORK_DIR         = atcity('augmentation/blender/current-scene')
EMPTY_SCENE_FILE = 'augmentation/scenes/empty-render.blend'
SCENES_INFO_NAME = 'scene.json'


def _copy_object_pose_ (src, dst):
    '''Copy location and dimensions from '''
    dims_src = src.dimensions
    dims_dst = dst.dimensions
    bpy.ops.object.select_all(action='DESELECT')
    dst.select = True
    value = Vector([dims_src[0] / dims_dst[0], dims_src[1] / dims_dst[1], 1])
    bpy.ops.transform.resize (value=value)
    dst.location = src.location
    bpy.ops.object.select_all(action='DESELECT')


def _copy_lamp_pose_ (src, dst):
    '''Copy location and dimensions of lamps (except location[z]). 
    They don't have dimensions, just scale. Scale is weird thou.'''
    center_src = src.location + src.dimensions / 2
    center_src = Vector([center_src[0], center_src[1], src.location[2]])
    dst.location = Vector([center_src[0], center_src[1], dst.location[2]])

    Scale_Unary = 2
    scale_dst = dst.scale
    dims_src = src.dimensions
    bpy.ops.object.select_all(action='DESELECT')
    dst.select = True
    value = Vector([dims_src[0] / scale_dst[0] * Scale_Unary, 
                    dims_src[1] / scale_dst[1] * Scale_Unary, 1])
    bpy.ops.transform.resize (value=value)
    bpy.ops.object.select_all(action='DESELECT')


def default_render_scene (scene_info):
    '''Takes the "Satellite" and "Camera" from the "input" file,
    Adjusts "empty-scene" file appropriately to create a scene for a video.
    '''
    in_path  = atcity(scene_info['in_render_file'])
    out_path = atcity(scene_info['out_render_file'])
    camera_info = scene_info['camera_info']

    # open the empty scene
    bpy.ops.wm.open_mainfile (filepath=atcity(EMPTY_SCENE_FILE))

    # remove everything unnecessary
    bpy.ops.object.select_all(action='DESELECT')  
    bpy.data.objects['-Car'].select = True
    bpy.data.objects['-Camera'].select = True
    bpy.ops.object.delete()

    # get Satellite and Camera info from .blend file
    with bpy.data.libraries.load(in_path, link=False) as (data_src, data_dst):
        data_dst.objects = ['-Satellite', '-Camera']
    # append Satellite
    satellite = data_dst.objects[0]
    assert satellite is not None
    bpy.context.scene.objects.link(satellite)
    # append Camera and set it active
    camera = data_dst.objects[1]
    assert camera is not None
    bpy.context.scene.objects.link(camera)
    bpy.context.scene.camera = camera

    # set camera resolution
    bpy.context.scene.render.resolution_x = camera_info['camera_dims']['width']
    bpy.context.scene.render.resolution_y = camera_info['camera_dims']['height']

    # adjust ground
    ground = bpy.data.objects['-Ground']
    _copy_object_pose_ (satellite, ground)
    ground.location = Vector([ground.location[0], ground.location[1], 0])

    # adjust sky
    _copy_lamp_pose_ (satellite, bpy.data.objects['-Sky-far-shadow'])
    _copy_lamp_pose_ (satellite, bpy.data.objects['-Sky-shadow'])

    # set sky-sunset (directed light) to be opposite to the camera
    rot_z = bpy.data.objects['-Camera'].rotation_euler[2]
    bpy.data.objects['-Sky-sunset'].rotation_euler[2] = rot_z

    assert op.exists(op.dirname(out_path)), 'out_path: %s' % out_path
    bpy.ops.wm.save_as_mainfile (filepath=out_path)




scene_info = json.load(open( op.join(WORK_DIR, SCENES_INFO_NAME) ))

default_render_scene (scene_info)

