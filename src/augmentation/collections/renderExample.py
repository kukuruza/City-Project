import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import json
import logging
import bpy
from learning.helperSetup import atcity, setupLogging
from augmentation.common import *
from augmentation.collections.utils import bounds

WORK_DIR = atcity('data/augmentation/blender/current-collection')



def render_example (model_id):

    # select the car as object
    obj = bpy.data.objects[model_id]
    obj.select = True

    # scale the DimsPlane to illustrate dimensions
    plane = bpy.data.objects['DimsPlane']
    plane.location = [0, 0, 0]

    roi = bounds(obj)
    dims = [roi.x.max-roi.x.min, roi.y.max-roi.y.min, roi.z.max-roi.z.min]
    dims = dict(zip(['x', 'y', 'z'], dims))

    plane.scale.x = dims['x'] * 0.5
    plane.scale.y = dims['y'] * 0.5

    # save a rendered example
    example_file = model['example_file']
    if not op.exists(atcity(op.dirname(example_file))): 
        os.makedirs(atcity(op.dirname(example_file)))
    logging.info ('writing example to %s' % example_file)
    render_scene(atcity(example_file))



if __name__ == '__main__':

    setupLogging('log/augmentation/renderExample.log', logging.DEBUG, 'a')

    model_path = op.join(WORK_DIR, 'model.json')
    model = json.load(open(model_path))

    valid = model['valid'] if 'valid' in model else True
    if not valid: 
        logging.info ('skip invalid model %s' % model['model_id'])
        sys.exit()

    model_id = model['model_id']
    logging.info ('processing model: %s' % model_id)

    scene_path = atcity('data/augmentation/scenes/empty-import.blend')
    bpy.ops.wm.open_mainfile(filepath=scene_path)

    try:
        import_blend_car (atcity(model['blend_file']), model_id)
    except:
        logging.error('could not import .blend model: %s' % atcity(model['blend_file']))
        model['error'] = 'blender cannot import .blend model'
        sys.exit()

    render_example (model_id)