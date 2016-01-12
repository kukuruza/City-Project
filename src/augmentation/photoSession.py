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
patches_dir = 'augmentation/patches/'

num_per_model = 1

SCALE_FACTOR = 1.5

SCALE_NOISE_SIGMA = 0.1
PITCH_LOW      = 20 * pi / 180
PITCH_HIGH     = 60 * pi / 180
SUN_PITCH_LOW  = 20 * pi / 180
SUN_PITCH_HIGH = 70 * pi / 180


def car_photo_session (num_per_model, car_sz, id_offset):
    '''Generate num_per_model renders of the car which is currently in the scene
    '''
    scales      = normal (1, SCALE_NOISE_SIGMA, size=num_per_model)
    yaws        = uniform (low=0, high=2*pi, size=num_per_model)
    pitches     = uniform (low=PITCH_LOW, high=PITCH_HIGH, size=num_per_model)

    sun_yaws    = uniform (low=0, high=2*pi, size=num_per_model)
    sun_pitches = uniform (low=SUN_PITCH_LOW, high=SUN_PITCH_HIGH, size=num_per_model)

    for i in range(num_per_model):

        scale = scales[i]
        yaw   = yaws[i]
        pitch = pitches[i]
        roll  = 0
        dist  = car_sz * SCALE_FACTOR / scale

        sun_yaw = sun_yaws[i]
        sun_pitch = sun_pitches[i]
        common.set_sun_angle (sun_yaw, sun_pitch)

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

# read the json file with cars data
collection = json.load(open( atcity(op.join(collection_dir, '_collection_.json')) ))

for vehicle_id, vehicle_info in enumerate(collection['vehicles']):

    print ('car name: "%s"' % vehicle_info['model_name'])
    if 'valid' in vehicle_info and vehicle_info['valid'] == False:
        print ('this model is marked broken, continue')
        continue

    car_ds = vehicle_info['dims']  # [x, y, z] in meters
    car_sz = sqrt(car_ds[0]*car_ds[0] + car_ds[1]*car_ds[1] + car_ds[2]*car_ds[2])

    obj_path = atcity(op.join(collection_dir, 'obj/%s.obj' % vehicle_info['model_id']))
    common.import_car (obj_path, 'car_group')

    # make a photo session at sunny weather
    common.set_dry()
    common.set_sunny()
    car_photo_session (num_per_model, car_sz, vehicle_id * 3)

    # make a photo session at cloudy weather
    common.set_dry()
    common.set_cloudy()
    car_photo_session (num_per_model, car_sz, vehicle_id * 3 + 1)

    # make a photo session at rainy weather
    common.set_wet()
    common.set_cloudy()
    car_photo_session (num_per_model, car_sz, vehicle_id * 3 + 2)

    common.delete_car ('car_group')

print ('finished photo session script')
