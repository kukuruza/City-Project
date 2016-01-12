import bpy
import os, os.path as op
import sys
import json
from math import cos, sin, pi, sqrt
import numpy as np
from numpy.random import normal, uniform
from mathutils import Color, Euler
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/augmentation'))
import common
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
from helperSetup import atcity

'''
Functions to parse blender output into images, masks, and annotations
This file knows about how we store data in SQL
'''

render_satellite = False
render_cars_as_cubes = False

NORMAL_FILENAME   = 'normal.png'
CARSONLY_FILENAME = 'cars-only.png'
CAR_RENDER_TEMPL  = 'vehicle-'


def position_car (car_group_name, x, y, yaw):
    '''Put the car to a certain position on the ground plane
    Args:
      car_group_name - name of a blender group
      x, y, yaw - target position in the blender x,y coordinate frame
    '''
    # TODO: now assumes object is at the origin.
    #       instead of transform, assign coords and rotation

    assert car_group_name in bpy.data.groups

    # deselect all
    bpy.ops.object.select_all(action='DESELECT')  
    
    # select objects in the group
    for obj in bpy.data.groups[car_group_name].objects:
        bpy.data.objects[obj.name].select = True

    bpy.ops.transform.translate (value=(x, y, 0))
    bpy.ops.transform.rotate (value=yaw * pi / 180, axis=(0,0,1))



collection_dir = 'augmentation/CAD/7c7c2b02ad5108fe5f9082491d52810'
render_dir = atcity('augmentation/render')
traffic_file = 'augmentation/traffic/traffic-572.json'


print ('start photo session script')

# read the json file with points to put
frame_info = json.load(open( atcity(traffic_file) ))
points  = frame_info['poses']
weather = frame_info['weather']

# set weather
if 'Dry'    in weather: common.set_dry()
if 'Wet'    in weather: common.set_wet()
if 'Cloudy' in weather: common.set_cloudy()
if 'Sunny'  in weather: common.set_sunny()

# render the image from satellite, when debuging
bpy.data.objects['-Satellite'].hide_render = not render_satellite

# place all cars
for i,point in enumerate(points):
    if render_cars_as_cubes:
        location = (point['x'], point['y'], 0.1)
        bpy.ops.mesh.primitive_cube_add(location=location, radius=0.3)
    else:
        collection_id = point['collection_id']
        model_id = point['model_id']
        obj_path = atcity(op.join(collection_dir, 'obj/%s.obj' % model_id))
        car_group_name = 'car_group_%i' % i
        common.import_car (obj_path, car_group_name)
        position_car (car_group_name, x=point['x'], y=point['y'], yaw=point['yaw'])



# render all cars and shadows
common.render_scene(op.join(render_dir, NORMAL_FILENAME))

# render all cars without ground plane
bpy.data.objects['-Ground'].hide_render = True
common.render_scene(op.join(render_dir, CARSONLY_FILENAME))

# render just the car for each car (to extract bbox)
if not render_cars_as_cubes:
    # hide all cars
    for i,point in enumerate(points):
        car_group_name = 'car_group_%i' % i
        common.hide_car (car_group_name)
    # show, render, and hide each car one by one
    for i,point in enumerate(points):
        car_group_name = 'car_group_%i' % i
        common.show_car (car_group_name)
        common.render_scene( op.join(render_dir, '%s%d.png' % (CAR_RENDER_TEMPL, i)) )
        common.hide_car (car_group_name)
    # show all cars
    for i,point in enumerate(points):
        car_group_name = 'car_group_%i' % i
        common.hide_car (car_group_name)


#bpy.ops.wm.save_as_mainfile (filepath='/Users/evg/Desktop/3Dmodel/test.blend')



