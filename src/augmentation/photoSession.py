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


COLLECTIONS_DIR  = atcity('augmentation/CAD')
PATCHES_HOME_DIR = atcity('augmentation/patches')
WORK_PATCHES_DIR = atcity('augmentation/blender/current-patch')
FRAME_INFO_NAME  = 'frame_info.json'
EXT = 'png'

WORK_DIR = '%s-%d' % (WORK_PATCHES_DIR, os.getppid())


SCALE_FACTOR = 1.5

SCALE_NOISE_SIGMA = 0.1
PITCH_LOW      = 10 * pi / 180
PITCH_HIGH     = 50 * pi / 180
SUN_ALTITUDE_LOW  = 20
SUN_ALTITUDE_HIGH = 70


def weather_photo_session (patches_dir, num_per_model, car_sz, id_offset):
    '''Generate num_per_model renders of the car which is currently in the scene
    '''
    scales      = normal (1, SCALE_NOISE_SIGMA, size=num_per_model)
    yaws        = uniform (low=0, high=2*pi, size=num_per_model)
    pitches     = uniform (low=PITCH_LOW, high=PITCH_HIGH, size=num_per_model)

    sun_azimuths  = uniform (low=0, high=360, size=num_per_model)
    sun_altitudes = uniform (low=SUN_ALTITUDE_LOW, high=SUN_ALTITUDE_HIGH, size=num_per_model)

    for i in range(num_per_model):

        scale = scales[i]
        yaw   = yaws[i]
        pitch = pitches[i]
        roll  = 0
        dist  = car_sz * SCALE_FACTOR / scale

        sun_azimuth = sun_azimuths[i]
        sun_altitude = sun_altitudes[i]
        common.set_sun_angle (sun_azimuth, sun_altitude)

        print ('scale: %.2f, yaw: %.2f, pitch: %.2f, roll: %.2f'
               % (scale, yaw*180/pi, pitch, roll))

        x = dist * cos(yaw) * cos(pitch)
        y = dist * sin(yaw) * cos(pitch)
        z = dist * sin(pitch)

        bpy.data.objects['-Camera'].location = (x,y,z)
        bpy.data.objects['-Sky-sunset'].location = (-x,-y,10)
        bpy.data.objects['-Sky-sunset'].rotation_euler = (60*pi/180, 0, yaw-pi/2)

        if not op.exists(patches_dir):
            os.makedirs(patches_dir)

        # render mask
        bpy.data.objects['-Ground'].hide_render = True
        bpy.context.scene.render.alpha_mode = 'TRANSPARENT'
        mask_name = '%08d-mask.%s' % (id_offset * num_per_model + i, EXT)
        common.render_scene(op.join(patches_dir, mask_name))

        # render normal
        bpy.data.objects['-Ground'].hide_render = False
        bpy.context.scene.render.alpha_mode = 'SKY'
        normal_name = '%08d-normal.%s' % (id_offset * num_per_model + i, EXT)
        common.render_scene(op.join(patches_dir, normal_name))

        #bpy.ops.wm.save_as_mainfile (filepath=op.join(patches_dir, 'out-%d.blend' % i))


def photo_session (vehicle):

    start_id      = vehicle['start_id']
    num_per_model = vehicle['num_per_model']
    collection_id = vehicle['collection_id']

    # open the blender file
    scene_path = atcity('augmentation/scenes/photo-session.blend')
    bpy.ops.wm.open_mainfile (filepath=scene_path)

    print ('car name: "%s"' % vehicle['model_name'])
    if 'valid' in vehicle and vehicle['valid'] == False:
        print ('this model is marked broken, continue')
        return

    dims = vehicle['dims']  # dict with 'x', 'y', 'z' in meters
    car_sz = sqrt(dims['x']*dims['x'] + dims['y']*dims['y'] + dims['z']*dims['z'])

    blend_path = op.join(COLLECTIONS_DIR, collection_id, 'blend/%s.blend' % vehicle['model_id'])
    common.import_blend_car (blend_path, vehicle['model_id'], 'car')

    patches_dir = op.join(PATCHES_HOME_DIR, collection_id, vehicle['model_id'])

    # make a photo session at sunny weather
    common.set_dry()
    common.set_sunny()
    weather_photo_session (patches_dir, num_per_model, car_sz, start_id*3)

    # make a photo session at cloudy weather
    common.set_dry()
    common.set_cloudy()
    weather_photo_session (patches_dir, num_per_model, car_sz, start_id*3+1)

    # make a photo session at rainy weather
    common.set_wet()
    common.set_cloudy()
    weather_photo_session (patches_dir, num_per_model, car_sz, start_id*3+2)

    common.delete_car ('car')




setupLogging('log/augmentation/photoSession.log', logging.INFO, 'a')

vehicle = json.load(open( op.join(WORK_DIR, FRAME_INFO_NAME) ))

photo_session (vehicle)

