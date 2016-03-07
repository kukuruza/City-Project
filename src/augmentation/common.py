import bpy
import os, os.path as op
import sys
import json
from math import cos, sin, pi, sqrt
import numpy as np
import logging
from numpy.random import normal, uniform
from mathutils import Color, Euler



def dump(obj):
   '''Helper function to output all properties of an object'''
   for attr in dir(obj):
       if hasattr( obj, attr ):
           print( "obj.%s = %s" % (attr, getattr(obj, attr)))



def render_scene (filepath):
    if op.exists(filepath): 
        os.remove(filepath)
    bpy.data.scenes['Scene'].render.filepath = filepath
    bpy.ops.render.render (write_still=True) 



def delete_car (car_name):
    assert car_name in bpy.data.objects, '%s' % car_name

    # deselect all
    bpy.ops.object.select_all(action='DESELECT')  
    
    bpy.data.objects[car_name].select = True
    bpy.ops.object.delete()



def import_car_obj (obj_path, car_group_name):
    assert car_group_name not in bpy.data.groups, '%s' % car_group_name

    car_group = bpy.data.groups.new(car_group_name)

    bpy.ops.import_scene.obj (filepath=obj_path)

    # add all new objects (they are all selected now) to the group
    for obj in bpy.context.selected_objects:
        bpy.context.scene.objects.active = obj
        bpy.ops.object.group_link (group=car_group_name)

    assert car_group_name in bpy.data.groups
    logging.debug ('in group "%s" there are %d objects' % 
        (car_group_name, len(bpy.data.groups[car_group_name].objects)))


def import_blend_car (blend_path, model_id, car_name=None):
    '''Import model_id object from blend_path .blend file, and rename it to car_name
    '''
    # append object from .blend file
    assert op.exists(blend_path)
    with bpy.data.libraries.load(blend_path, link=False) as (data_src, data_dst):
        data_dst.objects = [model_id]

    # link object to current scene
    obj = data_dst.objects[0]
    assert obj is not None
    bpy.context.scene.objects.link(obj)

    # raname
    if car_name is None: car_name = model_id
    obj.name = car_name
    logging.debug ('model_id %s imported' % model_id)



def join_car_meshes (model_id):
    ''' Join all meshes in a model_id group into a single object. Keep group
    Return:
        active object (joined model)
    '''
    for obj in bpy.data.groups[model_id].objects:
        bpy.data.objects[obj.name].select = True
    bpy.context.scene.objects.active = bpy.data.groups[model_id].objects[0]
    bpy.ops.object.join()
    bpy.context.scene.objects.active.name = model_id
    return bpy.context.scene.objects.active



def hide_car (car_name):
    '''Tags car object invisible'''
    assert car_name in bpy.data.objects

    bpy.data.objects[car_name].hide = True
    bpy.data.objects[car_name].hide_render = True


def show_car (car_name):
    '''Tags car object visible'''
    assert car_name in bpy.data.objects

    bpy.data.objects[car_name].hide = False
    bpy.data.objects[car_name].hide_render = False





def set_wet ():

    # pick the material
    mat = bpy.data.materials['Material-wet-asphalt']
    mat.mirror_color = (0.5, 0.5, 0.5)  # asphalt color
    #mat.use_only_shadow = True  # no ground plane (must be set)

    # assign the material to the ground
    ground = bpy.data.objects['-Ground']
    if len(ground.data.materials):
        ground.data.materials[0] = mat  # assign to 1st material slot
    else:
        ground.data.materials.append(mat)  # no slots


def set_dry ():

    # pick the material
    mat = bpy.data.materials['Material-dry-asphalt']
    mat.mirror_color = (0.5, 0.5, 0.5)  # asphalt color
    #mat.use_only_shadow = True  # no ground plane (must be set)

    # assign the material to the ground
    ground = bpy.data.objects['-Ground']
    if len(ground.data.materials):
        ground.data.materials[0] = mat  # assign to 1st material slot
    else:
        ground.data.materials.append(mat)  # no slots


def set_sunny ():

    # adjust sun
    sun = bpy.data.objects['-Sun']
    sun.hide_render = False
    sun.hide = False
    sun.data.energy = 1.5
    sun.data.color = (1.0000, 0.9163, 0.6905)

    # adjust sky
    sky = bpy.data.objects['-Sky-light']
    sky.hide_render = False
    sky.hide = False
    sky.data.energy = 0.25
    sky.data.color = (0.688, 0.795, 1.0)

    # turn off far shadows
    bpy.data.objects['-Sky-far-shadow'].hide = True
    bpy.data.objects['-Sky-far-shadow'].hide_render = True


def set_cloudy ():

    # adjust sun
    sun = bpy.data.objects['-Sun']
    sun.hide_render = True
    sun.hide = True

    # adjust sky
    sky = bpy.data.objects['-Sky-light']
    sky.hide_render = False
    sky.hide = False
    sky.data.energy = 0.75
    sky.data.color = (0.856, 0.827, 0.940)

    # turn on far shadows
    bpy.data.objects['-Sky-far-shadow'].hide = False
    bpy.data.objects['-Sky-far-shadow'].hide_render = False


def set_sun_angle (azimuth, altitude):
    '''
    Args:
      altitude: angle from surface, in degrees
      azimuth:  angle from the north, in degrees. On the east azimuth equals +90
    '''
    # note: azimuth lamp direction is the opposite to sun position
    yaw   = - (azimuth - 90) * pi / 180
    pitch = (90 - altitude) * pi / 180

    # set orientation
    sun = bpy.data.objects['-Sun']
    sun.rotation_euler = Euler((0, pitch, yaw), 'ZXY')

    # two opposite colors -- noon and sunset
    c_noon   = np.asarray([0.125, 0.151, 1])
    c_sunset = np.asarray([0, 0.274, 1])
    # get the mix between them according to the time of the day
    k = pitch / (pi/2)  # [0, 1], 0 -- noon, 1 - sunset
    c = Color()
    c.hsv = tuple(c_noon * (1 - k) + c_sunset * k)
    print ('set_sun_angle: pitch=%f, k=%f, c=(%.3f, %.3f, %.3f)' % (pitch, k, c[0], c[1], c[2]))
    sun.data.color = c


