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


collection_dir = 'augmentation/CAD/7c7c2b02ad5108fe5f9082491d52810'
patches_dir = 'augmentation/patches1/'

num_per_model = 1

SCALE_FACTOR = 1.5

SCALE_NOISE_SIGMA = 0.1
PITCH_LOW      = 20 * pi / 180
PITCH_HIGH     = 60 * pi / 180
SUN_ALTITUDE_LOW  = 20
SUN_ALTITUDE_HIGH = 70


def car_photo_session (num_per_model, car_sz, id_offset):
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
               % (scale, yaw, pitch, roll))

        png_name = '%08d.png' % (id_offset * num_per_model + i)
        x = dist * cos(yaw) * cos(pitch)
        y = dist * sin(yaw) * cos(pitch)
        z = dist * sin(pitch)

        bpy.data.objects['-Camera'].location = (x,y,z)

        bpy.data.scenes['Scene'].render.filepath = atcity(op.join(patches_dir, png_name))
        bpy.ops.render.render (write_still=True) 




print ('start photo session script')

# open the blender file
scene_path = atcity('augmentation/scenes/photo-session.blend')
bpy.ops.wm.open_mainfile (filepath=scene_path)

# read the json file with cars data
collection = json.load(open( atcity(op.join(collection_dir, 'readme.json')) ))

for i, vehicle in enumerate(collection['vehicles']):

    print ('car name: "%s"' % vehicle['model_name'])
    if 'valid' in vehicle and vehicle['valid'] == False:
        print ('this model is marked broken, continue')
        continue

    dims = vehicle['dims']  # dict with 'x', 'y', 'z' in meters
    car_sz = sqrt(dims['x']*dims['x'] + dims['y']*dims['y'] + dims['z']*dims['z'])

    blend_path = atcity(op.join(collection_dir, 'blend/%s.blend' % vehicle['model_id']))
    common.import_blend_car (blend_path, vehicle['model_id'], 'car')

    # make a photo session at sunny weather
    common.set_dry()
    common.set_sunny()
    car_photo_session (num_per_model, car_sz, i*3)

    # make a photo session at cloudy weather
    common.set_dry()
    common.set_cloudy()
    car_photo_session (num_per_model, car_sz, i*3+1)

    # make a photo session at rainy weather
    common.set_wet()
    common.set_cloudy()
    car_photo_session (num_per_model, car_sz, i*3+2)

    common.delete_car ('car')

print ('finished photo session script')
