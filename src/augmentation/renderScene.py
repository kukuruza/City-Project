import bpy
import os, os.path as op
import sys
import json
import logging
from math import cos, sin, pi, sqrt
import numpy as np
from numpy.random import normal, uniform
from mathutils import Color, Euler
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/augmentation'))
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/utilities'))
import common
from helperSetup import atcity, setupLogging

'''
Functions to parse blender output into images, masks, and annotations
This file knows about how we store data in SQL
'''

# debug option
render_satellite     = False
render_cars_as_cubes = False
save_blend_file      = False

# all inter-files name / path conventions
TRAFFIC_FILENAME  = 'traffic.json'
NORMAL_FILENAME   = 'normal.png'
CARSONLY_FILENAME = 'cars-only.png'
CAR_RENDER_TEMPL  = 'vehicle-'


def position_car (car_group_name, x, y, azimuth):
    '''Put the car to a certain position on the ground plane
    Args:
      car_group_name:  name of a blender group
      x, y:            target position in the blender x,y coordinate frame
      azimuth:         yaw angle in degrees, 0 is North and 90 deg. is East
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
    bpy.ops.transform.rotate (value=(90 - azimuth) * pi / 180, axis=(0,0,1))



def render_frame (frame_info, collection_dir, render_dir):
    '''Position cars in 3D according to input, and render frame
    Args:
      frame_info:  dictionary with frame information
      render_dir:  path to directory where to put all rendered images
    Returns:
      nothing
    '''

    logging.info ('started a frame')

    points  = frame_info['vehicles']
    weather = frame_info['weather']

    # set weather
    if 'Dry'    in weather: 
        logging.info ('setting dry weather')
        common.set_dry()
    if 'Wet'    in weather: 
        logging.info ('setting wet weather')
        common.set_wet()
    if 'Cloudy' in weather: 
        logging.info ('setting cloudy weather')
        common.set_cloudy()
    if 'Sunny'  in weather: 
        alt = frame_info['sun_altitude']
        azi = frame_info['sun_azimuth']
        logging.info ('setting sunny weather with azimuth,altitude = %f,%f' % (azi, alt))
        common.set_sunny()
        common.set_sun_angle(azi, alt)

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
            dae_path = atcity(op.join(collection_dir, 'dae/%s.dae' % model_id))
            car_group_name = 'car_group_%i' % i
            common.import_dae_car (dae_path, car_group_name)
            position_car (car_group_name, x=point['x'], y=point['y'], azimuth=point['azimuth'])

    # make all cars receive shadows
    logging.info ('materials: %s' % len(bpy.data.materials))
    for m in bpy.data.materials:
        m.use_transparent_shadows = True


    # create render dir
    if not op.exists(render_dir):
        os.makedirs(render_dir)

    # render all cars and shadows
    bpy.data.objects['-Ground'].hide_render = False
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

    bpy.data.objects['-Ground'].hide_render = False


    # delete all cars
    # for i,point in enumerate(points):
    #     car_group_name = 'car_group_%i' % i
    #     common.delete_car (car_group_name)

    if save_blend_file:
        # show all cars
        for i,point in enumerate(points):
            car_group_name = 'car_group_%i' % i
            common.show_car (car_group_name)
        bpy.ops.wm.save_as_mainfile (filepath=atcity(op.join(render_dir, 'out.blend')))

    # logging.info ('objects in the end of frame: %d' % len(bpy.data.objects))
    logging.info ('successfully finished a frame')
    


setupLogging('log/augmentation/renderScene.log', logging.INFO, 'a')

collection_dir = 'augmentation/CAD/7c7c2b02ad5108fe5f9082491d52810'
RENDER_DIR     = atcity('augmentation/render/current-frame')

frame_info = json.load(open( op.join(RENDER_DIR, TRAFFIC_FILENAME) ))

render_frame (frame_info, collection_dir, RENDER_DIR)
