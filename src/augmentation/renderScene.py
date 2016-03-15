import bpy
import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import json
import logging
import numpy as np
from augmentation.common import *
from learning.helperSetup import atcity, setupLogging, setParamUnlessThere

'''
Functions to parse blender output into images, masks, and annotations
This file knows about how we store data in SQL
'''

WORK_RENDER_DIR   = atcity('augmentation/blender/current-frame')
TRAFFIC_FILENAME  = 'traffic.json'

WORK_DIR = '%s-%d' % (WORK_RENDER_DIR, os.getppid())



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

    setParamUnlessThere (params, 'scale', 1)
    setParamUnlessThere (params, 'render_individual_cars', True)
    # debug options
    setParamUnlessThere (params, 'save_blend_file', False)
    setParamUnlessThere (params, 'render_satellite', False)
    setParamUnlessThere (params, 'render_cars_as_cubes', False)

    set_weather (params)

    # render the image from satellite, when debuging
    if '-Satellite' in bpy.data.objects:
        bpy.data.objects['-Satellite'].hide_render = not params['render_satellite']

    # make all cars receive shadows
    logging.info ('materials: %s' % len(bpy.data.materials))
    for m in bpy.data.materials:
        m.use_transparent_shadows = True


    # create render dir
    if not op.exists(render_dir):
        os.makedirs(render_dir)

    # render all cars and shadows
    bpy.data.objects['-Ground'].hide_render = False
    render_scene(op.join(render_dir, NORMAL_FILENAME))

    # render all cars without ground plane or sky
    bpy.context.scene.render.alpha_mode = 'TRANSPARENT'
    bpy.data.objects['-Ground'].hide_render = True
    render_scene(op.join(render_dir, CARSONLY_FILENAME))

    # render just the car for each car (to extract bbox)
    if params['render_individual_cars'] and not params['render_cars_as_cubes']:
        # hide all cars
        for car_name in car_names:
            hide_car (car_name)
        # show, render, and hide each car one by one
        for i,car_name in enumerate(car_names):
            show_car (car_name)
            render_scene( op.join(render_dir, '%s%d.png' % (CAR_RENDER_TEMPL, i)) )
            hide_car (car_name)

    # clean up
    bpy.data.objects['-Ground'].hide_render = False
    if not params['render_cars_as_cubes']:
        for car_name in car_names:
            show_car (car_name)

    if params['save_blend_file']:
        bpy.ops.wm.save_as_mainfile (filepath=atcity(op.join(render_dir, 'out.blend')))

    # logging.info ('objects in the end of frame: %d' % len(bpy.data.objects))
    logging.info ('make_snapshot: successfully finished a frame')
    



setupLogging('log/augmentation/processScene.log', logging.INFO, 'a')

frame_info = json.load(open( op.join(WORK_DIR, TRAFFIC_FILENAME) ))
setParamUnlessThere (frame_info, 'render_cars_as_cubes', False)

# place all cars
car_names = []
for i,vehicle in enumerate(frame_info['vehicles']):
    if frame_info['render_cars_as_cubes']:
        location = (vehicle['x'], vehicle['y'], 0.1)
        bpy.ops.mesh.primitive_cube_add(location=location, radius=0.3)
    else:
        collection_id = vehicle['collection_id']
        model_id = vehicle['model_id']
        blend_path = atcity(op.join('augmentation/CAD', collection_id, 'blend', '%s.blend' % model_id))
        car_name = 'car_%i' % i
        car_names.append(car_name)
        import_blend_car (blend_path, model_id, car_name)
        position_car (car_name, x=vehicle['x'], y=vehicle['y'], azimuth=vehicle['azimuth'])
        scale = frame_info['scale']
        bpy.ops.transform.resize (value=(scale, scale, scale))

make_snapshot (WORK_DIR, car_names, frame_info)
