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

render_satellite = False
render_cars_as_cubes = False

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



collection_dir = '/Users/evg/Downloads/7c7c2b02ad5108fe5f9082491d52810'
render_dir = '/Users/evg/Desktop/3Dmodel/renders'


print ('start photo session script')

# read the json file with cars data
vehicle_info = json.load(open( op.join(collection_dir, '_info_.json') ))

# read the json file with points to put
frame_json_path = '/Users/evg/Desktop/3Dmodel/572-car-poses.json'
frame_info = json.load(open( frame_json_path ))
points  = frame_info['poses']
weather = frame_info['weather']

# set weather
if 'Dry'    in weather: common.set_dry()
if 'Wet'    in weather: common.set_wet()
if 'Cloudy' in weather: common.set_cloudy()
if 'Sunny'  in weather: common.set_sunny()

# render the image from satellite, when debuggin
bpy.data.objects['-Satellite'].hide_render = not render_satellite

for i, point in enumerate(points):
    if render_cars_as_cubes:
        location = (point['x'], point['y'], 0.1)
        bpy.ops.mesh.primitive_cube_add(location=location, radius=0.3)
    else:
        model_id = vehicle_info['vehicles'][i]['model_id']
        obj_path = op.join(collection_dir, 'obj/%s.obj' % model_id)
        car_group_name = 'car_group_%d' % i
        common.import_car (obj_path, car_group_name)
        position_car (car_group_name, x=point['x'], y=point['y'], yaw=point['yaw'])


# render cars and shadows
shadows_path = op.join (render_dir, 'render-shadows.png')
bpy.data.scenes['Scene'].render.filepath = shadows_path
bpy.ops.render.render (write_still=True) 

# make ground plane invisible
sun = bpy.data.objects['-Ground']
sun.hide_render = True
sun.hide = True

# render cars only
carsonly_path = op.join (render_dir, 'render-cars-only.png')
bpy.data.scenes['Scene'].render.filepath = carsonly_path
bpy.ops.render.render (write_still=True) 

bpy.ops.wm.save_as_mainfile (filepath='/Users/evg/Desktop/3Dmodel/test.blend')



