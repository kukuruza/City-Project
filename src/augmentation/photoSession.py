import bpy
import os.path as op
import sys
import json
from math import cos, sin, pi, sqrt
import numpy as np
from numpy.random import normal, uniform
from mathutils import Color, Euler


def dump(obj):
   '''Helper function to output all properties of an object'''
   for attr in dir(obj):
       if hasattr( obj, attr ):
           print( "obj.%s = %s" % (attr, getattr(obj, attr)))


def delete_car (car_group_name):
    assert car_group_name in bpy.data.groups

    # deselect all
    bpy.ops.object.select_all(action='DESELECT')  
    
    # select objects in the group
    for obj in bpy.data.groups[car_group_name].objects:
        bpy.data.objects[obj.name].select = True

    # remove all selected.
    bpy.ops.object.delete()
    assert len(bpy.context.selected_objects) == 0
    assert len(bpy.data.groups['car_group'].objects) == 0

    # TODO: remove group too


def import_car (obj_path, car_group_name):

    # new or existing group
    if car_group_name in bpy.data.groups:
        # if exists, delete everything in there (TODO: change when group removed)
        delete_car (car_group_name)
        print ('group already existed, had to clean it first')
    else:
        car_group = bpy.data.groups.new(car_group_name)

    bpy.ops.import_scene.obj (filepath=obj_path)

    # add all new objects (they are all selected now) to the group
    for obj in bpy.context.selected_objects:
        bpy.context.scene.objects.active = obj
        bpy.ops.object.group_link (group=car_group_name)

    assert car_group_name in bpy.data.groups
    print ('in group "%s" there are %d objects' % 
           (car_group_name, len(bpy.data.groups[car_group_name].objects)))


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



collection_dir = '/Users/evg/Downloads/7c7c2b02ad5108fe5f9082491d52810'
png_dir = '/Users/evg/Downloads/patches/'

NUM_SAMPLES = 2

SCALE_FACTOR = 1.5

SCALE_NOISE_SIGMA = 0.1
PITCH_LOW      = 20 * pi / 180
PITCH_HIGH     = 60 * pi / 180
SUN_PITCH_LOW  = 20 * pi / 180
SUN_PITCH_HIGH = 70 * pi / 180


def car_photo_session (car_sz, id_offset):
    '''Generate NUM_SAMPLES renders of the car which is currently in the scene
    '''
    scales      = normal (1, SCALE_NOISE_SIGMA, size=NUM_SAMPLES)
    yaws        = uniform (low=0, high=2*pi, size=NUM_SAMPLES)
    pitches     = uniform (low=PITCH_LOW, high=PITCH_HIGH, size=NUM_SAMPLES)

    sun_yaws    = uniform (low=0, high=2*pi, size=NUM_SAMPLES)
    sun_pitches = uniform (low=SUN_PITCH_LOW, high=SUN_PITCH_HIGH, size=NUM_SAMPLES)

    for i in range(NUM_SAMPLES):

        scale = scales[i]
        yaw   = yaws[i]
        pitch = pitches[i]
        roll  = 0
        dist  = car_sz * SCALE_FACTOR / scale

        sun_yaw = sun_yaws[i]
        sun_pitch = sun_pitches[i]
        set_sun_angle (sun_yaw, sun_pitch)

        print ('scale: %.2f, yaw: %.2f, pitch: %.2f, roll: %.2f'
               % (scale, yaw, pitch, roll))

        png_name = '%08d.png' % (id_offset * NUM_SAMPLES + i)
        x = dist * cos(yaw) * cos(pitch)
        y = dist * sin(yaw) * cos(pitch)
        z = dist * sin(pitch)

        bpy.data.objects['-Camera'].location = (x,y,z)

        bpy.data.scenes['Scene'].render.filepath = op.join (png_dir, png_name)
        bpy.ops.render.render (write_still=True) 




print ('start photo session script')

# read the json file with cars data
info = json.load(open( op.join(collection_dir, '_info_.json') ))

for vehicle_id, vehicle_info in enumerate(info['vehicles']):

    print ('car name: "%s"' % vehicle_info['model_name'])
    if 'valid' in vehicle_info and vehicle_info['valid'] == False:
        print ('this model is marked broken, continue')
        continue

    car_ds = vehicle_info['dims']  # [x, y, z] in meters
    car_sz = sqrt(car_ds[0]*car_ds[0] + car_ds[1]*car_ds[1] + car_ds[2]*car_ds[2])

    obj_path = op.join(collection_dir, 'obj/%s.obj' % vehicle_info['model_id'])
    import_car (obj_path, 'car_group')

    # make a photo session at sunny weather
    set_dry()
    set_sunny()
    car_photo_session (car_sz, vehicle_id * 3)

    # make a photo session at cloudy weather
    set_dry()
    set_cloudy()
    car_photo_session (car_sz, vehicle_id * 3 + 1)

    # make a photo session at rainy weather
    set_wet()
    set_cloudy()
    car_photo_session (car_sz, vehicle_id * 3 + 2)

    delete_car ('car_group')

print ('finished photo session script')
