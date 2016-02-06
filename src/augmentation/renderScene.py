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
import common
from helperSetup import atcity, setupLogging

'''
Functions to parse blender output into images, masks, and annotations
This file knows about how we store data in SQL
'''

# debug option
render_satellite     = False
render_cars_as_cubes = False
save_blend_file      = True

# all inter-files name / path conventions
TRAFFIC_FILENAME  = 'traffic.json'
NORMAL_FILENAME   = 'normal.png'
CARSONLY_FILENAME = 'cars-only.png'
CAR_RENDER_TEMPL  = 'vehicle-'


def position_car (car_name, x, y, azimuth):
    '''Put the car to a certain position on the ground plane
    Args:
      car_name:        name of the blender model
      x, y:            target position in the blender x,y coordinate frame
      azimuth:         angle in degrees, 0 is North (y-axis) and 90 deg. is East
    '''
    # TODO: now assumes object is at the origin.
    #       instead of transform, assign coords and rotation

    assert car_name in bpy.data.objects

    # select only car
    bpy.ops.object.select_all(action='DESELECT')  
    bpy.data.objects[car_name].select = True

    bpy.ops.transform.translate (value=(x, y, 0))
    bpy.ops.transform.rotate (value=(90 - azimuth) * pi / 180, axis=(0,0,1))



def render_frame (frame_info, render_dir):
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
    scale   = frame_info['scale'] 

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
            blend_path = atcity(op.join('augmentation/CAD', collection_id, 'blend', '%s.blend' % model_id))
            car_name = 'car_%i' % i
            common.import_blend_car (blend_path, model_id, car_name)
            position_car (car_name, x=point['x'], y=point['y'], azimuth=point['azimuth'])
            bpy.ops.transform.resize (value=(scale, scale, scale))

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
            car_name = 'car_%i' % i
            common.hide_car (car_name)
        # show, render, and hide each car one by one
        for i,point in enumerate(points):
            car_name = 'car_%i' % i
            common.show_car (car_name)
            common.render_scene( op.join(render_dir, '%s%d.png' % (CAR_RENDER_TEMPL, i)) )
            common.hide_car (car_name)

    bpy.data.objects['-Ground'].hide_render = False


    if save_blend_file:
        # show all cars
        if not render_cars_as_cubes:
            for i,point in enumerate(points):
                car_name = 'car_%i' % i
                common.show_car (car_name)
        bpy.ops.wm.save_as_mainfile (filepath=atcity(op.join(render_dir, 'out.blend')))

    # NOT USED now because the .blend file is discarded after this
    # delete all cars
    #for i,point in enumerate(points):
    #    car_name = 'car_%i' % i
    #    common.delete_car (car_name)

    # logging.info ('objects in the end of frame: %d' % len(bpy.data.objects))
    logging.info ('successfully finished a frame')
    


#bpy.context.user_preferences.system.compute_device_type = 'CUDA'
#bpy.context.user_preferences.system.compute_device = 'CUDA_0'

setupLogging('log/augmentation/processScene.log', logging.INFO, 'a')

RENDER_DIR     = atcity('augmentation/render/current-frame')

frame_info = json.load(open( op.join(RENDER_DIR, TRAFFIC_FILENAME) ))

render_frame (frame_info, RENDER_DIR)
