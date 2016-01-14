import bpy
import os.path as op
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
    bpy.data.scenes['Scene'].render.filepath = filepath
    bpy.ops.render.render (write_still=True) 



def delete_car (car_group_name):
    assert car_group_name in bpy.data.groups, '%s' % car_group_name

    # deselect all
    bpy.ops.object.select_all(action='DESELECT')  
    
    # select objects in the group
    for obj in bpy.data.groups[car_group_name].objects:
        bpy.data.objects[obj.name].select = True

    # remove all selected.
    bpy.ops.object.delete()
    assert len(bpy.context.selected_objects) == 0
    assert len(bpy.data.groups[car_group_name].objects) == 0

    # remove group itself
    bpy.data.groups.remove(bpy.data.groups[car_group_name])



def import_car (obj_path, car_group_name):
    assert car_group_name not in bpy.data.groups, '%s' % car_group_name

    car_group = bpy.data.groups.new(car_group_name)

    bpy.ops.import_scene.obj (filepath=obj_path)

    # add all new objects (they are all selected now) to the group
    for obj in bpy.context.selected_objects:
        bpy.context.scene.objects.active = obj
        bpy.ops.object.group_link (group=car_group_name)

    assert car_group_name in bpy.data.groups
    print ('in group "%s" there are %d objects' % 
           (car_group_name, len(bpy.data.groups[car_group_name].objects)))


def hide_car (car_group_name):
    '''Tags each object in a car group invisible'''
    assert car_group_name in bpy.data.groups

    # hide each object in the group
    for obj in bpy.data.groups[car_group_name].objects:
        bpy.data.objects[obj.name].hide = True
        bpy.data.objects[obj.name].hide_render = True


def show_car (car_group_name):
    '''Tags each object in a car group visible'''
    assert car_group_name in bpy.data.groups

    # hide each object in the group
    for obj in bpy.data.groups[car_group_name].objects:
        bpy.data.objects[obj.name].hide = False
        bpy.data.objects[obj.name].hide_render = False





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
    sun.data.energy = 1
    sun.data.color = (1.0000, 0.9163, 0.6905)

    # adjust sky
    sky = bpy.data.objects['-Sky-light']
    sky.hide_render = False
    sky.hide = False
    sky.data.energy = 1.5
    sky.data.color = (0.537, 0.720, 1.0)


def set_cloudy ():

    # adjust sun
    sun = bpy.data.objects['-Sun']
    sun.hide_render = True
    sun.hide = True

    # adjust sky
    sky = bpy.data.objects['-Sky-light']
    sky.hide_render = False
    sky.hide = False
    sky.data.energy = 1
    sky.data.color = (0.856, 0.827, 0.940)


def set_sun_angle (yaw, pitch):
    '''pitch -- angle from zenith, in radians
    '''
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


