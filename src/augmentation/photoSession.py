import bpy
import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import json
import logging
from math import cos, sin, pi, sqrt, ceil
import numpy as np
from random import choice
from numpy.random import normal, uniform
from mathutils import Color, Euler
from augmentation.common import *
from learning.helperSetup import atcity, setupLogging
from learning.helperSetup import setParamUnlessThere, assertParamIsThere



COLLECTIONS_DIR  = atcity('augmentation/CAD')
WORK_PATCHES_DIR = atcity('augmentation/blender/current-patch')
JOB_INFO_NAME    = 'job_info.json'

NORMAL_FILENAME   = 'normal.png'
CARSONLY_FILENAME = 'cars-only.png'
CAR_RENDER_TEMPL  = 'vehicle-'

WORK_DIR = '%s-%d' % (WORK_PATCHES_DIR, os.getppid())


SCALE_FACTOR = 3   # how far a camera is from the origin

# sampling weather and camera position
SCALE_NOISE_SIGMA = 0.1
PITCH_LOW         = 5 * pi / 180
PITCH_HIGH        = 30 * pi / 180
SUN_ALTITUDE_MIN  = 20
SUN_ALTITUDE_MAX  = 70


def prepare_photo (car_sz):
    '''Pick some random parameters, adjust lighting, and finally render a frame
    '''
    # pick random weather
    params = {}
    params['sun_azimuth']  = uniform(low=0, high=360)
    params['sun_altitude'] = uniform(low=SUN_ALTITUDE_MIN, high=SUN_ALTITUDE_MAX)
    params['weather'] = choice([['Dry','Sunny'], ['Dry','Cloudy'], ['Wet','Cloudy']])

    # pick random camera angle and distance
    scale = normal (1, SCALE_NOISE_SIGMA)
    azimuth  = uniform (low=0, high=2*pi)
    altitude = uniform (low=PITCH_LOW, high=PITCH_HIGH)
    print ('scale: %.2f, azimuth: %.2f, altitude: %.2f' % 
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

    params['save_blend_file'] = False
    params['azimuth'] = azimuth
    params['altitude'] = altitude
    return params



def make_snapshot (render_dir, car_names, params):
    '''Set up the weather, and render vehicles into files:
      NORMAL, CARSONLY, and CAR_RENDER_TEMPL
    Args:
      render_dir:  path to directory where to put all rendered images
      car_names:   names of car objects in the scene
      params:      dictionary with frame information
    Returns:
      nothing
    '''
    logging.info ('make_snapshot: started')
    setParamUnlessThere (params, 'save_blend_file', False)

    # create render dir
    if not op.exists(render_dir):
        os.makedirs(render_dir)

    # nodes to change output paths
    render_node = bpy.context.scene.node_tree.nodes['render']
    depth_node  = bpy.context.scene.node_tree.nodes['depth']

    set_weather (params)

    ### render all cars and shadows

    render_node.base_path = atcity(render_dir)
    depth_node.base_path  = '/dev/null'

    # make all cars receive shadows
    logging.info ('materials: %s' % len(bpy.data.materials))
    for m in bpy.data.materials:
        m.use_transparent_shadows = True

    # gray ground and sky
    bpy.data.scenes['Scene'].render.use_textures = True
    bpy.data.scenes['Scene'].render.use_shadows  = True
    bpy.data.scenes['Scene'].render.use_raytrace = True
    bpy.data.objects['-Ground'].hide_render = False
    bpy.context.scene.render.alpha_mode = 'SKY'

    bpy.ops.render.render (write_still=True)

    # move to a better name
    assert op.exists(atcity(op.join(render_dir, 'Image0001'))), 'didnt render color'
    os.rename(atcity(op.join(render_dir, 'Image0001')), 
              atcity(op.join(render_dir, 'render.png')))

    ### depth maps

    bpy.data.scenes['Scene'].render.use_textures = False
    bpy.data.scenes['Scene'].render.use_shadows  = False
    bpy.data.scenes['Scene'].render.use_raytrace = False
    bpy.context.scene.render.alpha_mode = 'TRANSPARENT'
    bpy.data.objects['-Ground'].hide_render = True

    # for all cars

    # TODO: do smth so that it doesn't say it can't write file
    render_node.base_path = '/dev/null'
    depth_node.base_path  = atcity(render_dir)
    bpy.ops.render.render (write_still=True)

    # move to a better name
    assert op.exists(atcity(op.join(render_dir, 'Image0001'))), 'didnt render all depth'
    os.rename(atcity(op.join(render_dir, 'Image0001')), 
              atcity(op.join(render_dir, 'depth-all.png')))

    # for the main car

    # hide all cars except the first (main) one
    for car_name in car_names[1:]:
        hide_car (car_name)

    # TODO: do smth so that it doesn't say it can't write file
    render_node.base_path = '/dev/null'
    depth_node.base_path  = atcity(render_dir)
    bpy.ops.render.render (write_still=True)

    # move to a better name
    assert op.exists(atcity(op.join(render_dir, 'Image0001'))), 'didnt render main depth'
    os.rename(atcity(op.join(render_dir, 'Image0001')), 
              atcity(op.join(render_dir, 'depth-car.png')))

    ### aftermath
    
    # hide all cars except the first (main) one
    for car_name in car_names:
        show_car (car_name)

    if params['save_blend_file']:
        bpy.ops.wm.save_as_mainfile (filepath=atcity(op.join(render_dir, 'out.blend')))

    ### write down some labelling info
    angles_path = atcity(op.join(render_dir, 'angles.json'))
    with open(angles_path, 'w') as f:
        f.write(json.dumps({'azimuth':  params['azimuth'] * 180 / pi,
                            'altitude': params['altitude'] * 180 / pi}, indent=4))

    logging.info ('make_snapshot: successfully finished a frame')
    


def photo_session (job):
    '''Take pictures of a scene from different random angles, 
      given some cars placed and fixed in the scene.
    '''
    num_per_session = job['num_per_session']
    vehicles        = job['vehicles']

    # open the blender file
    scene_path = atcity('augmentation/scenes/photo-session.blend')
    bpy.ops.wm.open_mainfile (filepath=scene_path)

    setParamUnlessThere (job, 'render_width',  200)
    setParamUnlessThere (job, 'render_height', 150)
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

    # take snapeshots from different angles
    dims = vehicles[0]['dims']  # dict with 'x', 'y', 'z' in meters
    car_sz = sqrt(dims['x']*dims['x'] + dims['y']*dims['y'] + dims['z']*dims['z'])
    for i in range(num_per_session):
        render_dir = op.join(WORK_DIR, '%06d' % i)
        make_snapshot (render_dir, car_names, prepare_photo(car_sz))




setupLogging('log/augmentation/photoSession.log', logging.DEBUG, 'a')

job = json.load(open( op.join(WORK_DIR, JOB_INFO_NAME) ))

photo_session (job)

