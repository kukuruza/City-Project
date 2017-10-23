import bpy
import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import json
import logging
from math import cos, sin, pi, sqrt, ceil
import numpy as np
from glob import glob
from random import choice
from numpy.random import normal, uniform
from mathutils import Color, Euler
from augmentation.common import *
from db.lib.helperSetup import atcity, setupLogging



COLLECTIONS_DIR  = atcity('data/augmentation/CAD')
ROAD_TEXTURE_DIR = atcity('data/augmentation/resources/textures/road')
BLDG_TEXTURE_DIR = atcity('data/augmentation/resources/textures/buildings')
WORK_PATCHES_DIR = atcity('data/augmentation/blender/current-patch')
JOB_INFO_NAME    = 'job_info.json'
OUT_INFO_NAME    = 'out_info.json'

WORK_DIR = '%s-%d' % (WORK_PATCHES_DIR, os.getppid())


SCALE_FACTOR = 2   # how far a camera is from the origin
RENDER_WIDTH  = 400
RENDER_HEIGHT = 400

# sampling weather and camera position
SCALE_NOISE_SIGMA = 0.1
PITCH_LOW         = 20 * pi / 180
PITCH_HIGH        = 40 * pi / 180
SUN_ALTITUDE_MIN  = 20
SUN_ALTITUDE_MAX  = 70


def prepare_simplest_photo (car_sz, azimuth_low, azimuth_high):
    '''Pick only random camera pose, and finally render a frame
    '''
    # pick random weather
    params = {}
    params['weather'] = 'Cloudy'
    set_weather (params)
    # turn off sky reflexion
    bpy.data.lamps['Sky-sunset'].energy = 0

    # pick random camera angle and distance
    scale = normal (1, SCALE_NOISE_SIGMA)
    azimuth  = uniform (low=azimuth_low, high=azimuth_high)
    altitude = uniform (low=PITCH_LOW, high=PITCH_HIGH)
    print ('scale: %.2f, azimuth: %.2f, altitude: %.2f' % 
           (scale, azimuth*180/pi, altitude))

    # compute camera position
    dist  = car_sz * SCALE_FACTOR / scale
    x = dist * cos(azimuth) * cos(altitude)
    y = dist * sin(azimuth) * cos(altitude)
    z = dist * sin(altitude)
    bpy.data.objects['-Camera'].location = (x,y,z)

    # hide everything
    bpy.data.objects['-Building'].hide_render = True
    bpy.data.objects['-Ground'].hide_render = True

    params['azimuth'] = azimuth * 180 / pi
    params['altitude'] = altitude * 180 / pi

    return params



def prepare_photo (car_sz, azimuth_low, azimuth_high):
    '''Pick some random parameters, adjust lighting, and finally render a frame
    '''
    # pick random weather
    params = {}
    params['sun_azimuth']  = uniform(low=0, high=360)
    params['sun_altitude'] = uniform(low=SUN_ALTITUDE_MIN, high=SUN_ALTITUDE_MAX)
    params['weather'] = choice(['Rainy', 'Cloudy', 'Sunny', 'Wet'])
    set_weather (params)

    # pick random camera angle and distance
    scale = normal (1, SCALE_NOISE_SIGMA)
    azimuth  = uniform (low=azimuth_low, high=azimuth_high)
    altitude = uniform (low=PITCH_LOW, high=PITCH_HIGH)
    logging.info ('prepare_photo: scale: %.2f, azimuth (deg): %.2f, altitude: %.2f' % 
           (scale, azimuth*180/pi, altitude))

    # compute camera position
    dist  = car_sz * SCALE_FACTOR / scale
    x = dist * cos(azimuth) * cos(altitude)
    y = dist * sin(azimuth) * cos(altitude)
    z = dist * sin(altitude)

    # set up lighting
    bpy.data.objects['-Camera'].location = (x,y,z)
    bpy.data.objects['-Sky-sunset'].location = (-x,-y,10)
    bpy.data.objects['-Sky-sunset'].rotation_euler = (60*pi/180, 0, azimuth-pi/2)

    # set up road
    # assign a random texture from the directory
    road_texture_path = choice(glob(op.join(ROAD_TEXTURE_DIR, '*.jpg')))
    logging.info ('road_texture_path: %s' % road_texture_path)
    bpy.data.images['ground'].filepath = road_texture_path
    # pick a random road width
    road_width = normal(15, 5)
    bpy.data.objects['-Ground'].dimensions.x = road_width

    # set up building
    # assign a random texture from the directory
    buidling_texture_path = choice(glob(op.join(BLDG_TEXTURE_DIR, '*.jpg')))
    logging.info ('buidling_texture_path: %s' % buidling_texture_path)
    bpy.data.images['building'].filepath = buidling_texture_path
    # put the building at the edge of the road, opposite to the camera
    bpy.data.objects['-Building'].location.y = road_width/2 * (1 if y < 0 else -1)
    # pick a random height dim
    bpy.data.objects['-Building'].dimensions.z = normal(20, 5)
    # move randomly along a X and Z axes
    bpy.data.objects['-Building'].location.x = normal(0, 5)
    bpy.data.objects['-Building'].location.z = uniform(-5, 0)

    params['azimuth'] = azimuth * 180 / pi
    params['altitude'] = altitude * 180 / pi

    return params



def make_snapshot (render_dir, car_names, params):
    '''Set up the weather, and render vehicles into files
    Args:
      render_dir:  path to directory where to put all rendered images
      car_names:   names of car objects in the scene
      params:      dictionary with frame information
    Returns:
      nothing
    '''
    logging.info ('make_snapshot: started')

    # create render dir
    print (atcity(render_dir))
    if not op.exists(atcity(render_dir)):
        os.makedirs(atcity(render_dir))

    # nodes to change output paths
    bpy.context.scene.node_tree.nodes['render'].base_path = atcity(render_dir)
    bpy.context.scene.node_tree.nodes['depth-all'].base_path = atcity(render_dir)
    bpy.context.scene.node_tree.nodes['depth-car'].base_path = atcity(render_dir)

    # make all cars receive shadows
    logging.info ('materials: %s' % len(bpy.data.materials))
    for m in bpy.data.materials:
        m.use_transparent_shadows = True

    # add cars to Cars and Depth-all layers and the main car to Depth-car layer
    for car_name in car_names:
        for layer_id in range(3):
            bpy.data.objects[car_name].layers[layer_id] = False
    for car_name in car_names:
        bpy.data.objects[car_name].layers[0] = True
        bpy.data.objects[car_name].layers[1] = True
    bpy.data.objects[car_names[0]].layers[2] = True

    # render scene
    bpy.ops.render.render (write_still=True, layer='Cars')

    # change the names of output png files
    for layer_name in ['render', 'depth-all', 'depth-car']:
        os.rename(atcity(op.join(render_dir, '%s0001' % layer_name)), 
                  atcity(op.join(render_dir, '%s.png' % layer_name)))

    ### aftermath
    
    for car_name in car_names:
        show_car (car_name)

    logging.info ('make_snapshot: successfully finished a frame')
    return params
    


def photo_session (job):
    '''Take pictures of a scene from different random angles, 
      given some cars placed and fixed in the scene.
    '''
    num_per_session = job['num_per_session']
    vehicles        = job['vehicles']

    azimuth_low     = job['azimuth_low']
    azimuth_high    = job['azimuth_high']

    # open the blender file
    scene_path = atcity('data/augmentation/scenes/photo-session.blend')
    bpy.ops.wm.open_mainfile (filepath=scene_path)

    if 'render_width' not in job: job['render_width'] = RENDER_WIDTH
    if 'render_height' not in job: job['render_height'] = RENDER_HEIGHT
    bpy.context.scene.render.resolution_x = job['render_width']
    bpy.context.scene.render.resolution_y = job['render_height']

    car_names = []
    for i,vehicle in enumerate(vehicles):
        blend_path = op.join(COLLECTIONS_DIR, vehicle['collection_id'], 
                             'blend/%s.blend' % vehicle['model_id'])

        assert op.exists(blend_path), 'blend path does not exist' % blend_path
        # if 'dims' not in vehicle or not op.exists(blend_path):
        #     logging.error ('dims or blend_path does not exist. Skip.')
        #     continue

        car_name = 'car-%d' % i
        car_names.append(car_name)
        import_blend_car (blend_path, vehicle['model_id'], car_name)
        position_car (car_name, vehicles[i]['x'], vehicles[i]['y'], vehicles[i]['azimuth'])

    # take snapshots from different angles
    dims = vehicles[0]['dims']  # dict with 'x', 'y', 'z' in meters
    car_sz = sqrt(dims['x']*dims['x'] + dims['y']*dims['y'] + dims['z']*dims['z'])
    for i in range(num_per_session):
        render_dir = op.join(WORK_DIR, '%06d' % i)
        params = make_snapshot (render_dir, car_names, 
                                prepare_photo(car_sz, azimuth_low, azimuth_high))

        if job['save_blender']:
            bpy.ops.wm.save_as_mainfile (filepath=atcity(op.join(render_dir, 'out.blend')))

        ### write down some labelling info
        out_path = atcity(op.join(render_dir, OUT_INFO_NAME))
        with open(out_path, 'w') as f:
            f.write(json.dumps({'azimuth':      (180 - params['azimuth']) % 360, # match KITTI
                                'altitude':     params['altitude'],
                                'vehicle_type': vehicles[0]['vehicle_type'],
                                'model_id':     vehicles[0]['model_id']}, indent=4))



setupLogging('log/augmentation/photoSession.log', logging.DEBUG, 'a')

job = json.load(open( op.join(WORK_DIR, JOB_INFO_NAME) ))

photo_session (job)

