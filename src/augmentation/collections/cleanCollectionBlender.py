import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import json
import logging
import collections
import time
import shutil
from math import cos, sin, pi, sqrt
import bpy
from mathutils import Vector
from learning.helperSetup import atcity, setupLogging
from augmentation.common import *

WORK_DIR = atcity('data/augmentation/blender/current-collection')



width_true = {'truck': 2.5, 'van': 2.2, 'taxi': 1.9, 
              'sedan': 1.9, 'bus': 2.5, 'schoolbus': 2.5,
              'vehicle': 2.5}


class MinHeightException(Exception):
    pass


class Timer(object):
    """A simple timer."""
    def __init__(self):
        self.total_time = 0.
        self.calls = 0
        self.start_time = 0.
        self.diff = 0.
        self.average_time = 0.

    def tic(self):
        # using time.time instead of time.clock because time time.clock
        # does not normalize for multithreading
        self.start_time = time.time()

    def toc(self, average=True):
        self.diff = time.time() - self.start_time
        self.total_time += self.diff
        self.calls += 1
        self.average_time = self.total_time / self.calls
        if average:
            return self.average_time
        else:
            return self.diff


def bounds(obj, local=False):
    '''Usage:
        object_details = bounds(obj)
        a = object_details.z.max
        b = object_details.z.min
        c = object_details.z.distance
    '''

    local_coords = obj.bound_box[:]
    om = obj.matrix_world

    if not local:    
        worldify = lambda p: om * Vector(p[:]) 
        coords = [worldify(p).to_tuple() for p in local_coords]
    else:
        coords = [p[:] for p in local_coords]

    rotated = zip(*coords[::-1])

    push_axis = []
    for (axis, _list) in zip('xyz', rotated):
        info = lambda: None
        info.max = max(_list)
        info.min = min(_list)
        info.distance = info.max - info.min
        push_axis.append(info)

    originals = dict(zip(['x', 'y', 'z'], push_axis))

    o_details = collections.namedtuple('object_details', 'x y z')
    return o_details(**originals)



def get_origin_and_dims (car_group_name, height_ratio = 0.33, min_count = 10):
    '''Find car origin and dimensions by taking max dimensions below mirrors.
    Args:
    Returns:
      origin:  Dict with 'x', 'y', 'z' entries. 
               'x' and 'y' = center of the car body (no mirrors), 'z' = min(z)
      dims:    Dict with 'x', 'y', 'z'
               'x' and 'y' = dimensions of the car body (no mirrors)
    '''
    # find the z dimensions of the car
    z_min = 1000
    z_max = -1000

    for obj in bpy.data.groups[car_group_name].objects:
        roi = bounds(obj)
        z_min = min(roi.z.min, z_min)
        z_max = max(roi.z.max, z_max)
    logging.info ('z_min = %f, z_max = %f' % (z_min, z_max))

    # find x and y dimensions for everything below third height
    y_min_body = y_min_mirrors = 1000
    y_max_body = y_max_mirrors = -1000
    x_min_body = x_min_mirrors = 1000
    x_max_body = x_max_mirrors = -1000
    count_below_height_ratio = 0
    for obj in bpy.data.groups[car_group_name].objects:
        roi = bounds(obj)
        # update total (with mirrors and other expanding stuff) dimensions
        y_min_mirrors = min(roi.y.min, y_min_mirrors)
        y_max_mirrors = max(roi.y.max, y_max_mirrors)
        x_min_mirrors = min(roi.x.min, x_min_mirrors)
        x_max_mirrors = max(roi.x.max, x_max_mirrors)
        # update body dimensions
        if (roi.z.min + roi.z.max) / 2 < z_min + (z_max - z_min) * height_ratio:
            y_min_body = min(roi.y.min, y_min_body)
            y_max_body = max(roi.y.max, y_max_body)
            x_min_body = min(roi.x.min, x_min_body)
            x_max_body = max(roi.x.max, x_max_body)
            count_below_height_ratio += 1
    # check the number of objects that are low enough
    count_all = len(bpy.data.groups[car_group_name].objects)
    logging.debug ('out of %d objects, %d are below height_ratio %f' % \
        (count_all, count_below_height_ratio, height_ratio))
    if count_below_height_ratio < min_count:
        raise MinHeightException('not enough objects below %.2f of height' % height_ratio)

    # verbose output
    length_body    = x_max_body - x_min_body
    width_body     = y_max_body - y_min_body
    width_mirrors  = y_max_mirrors - y_min_mirrors    
    logging.debug ('mirrors dims: %.2f < y < %.2f' % (y_min_mirrors, y_max_mirrors))
    logging.debug ('body dims:    %.2f < y < %.2f' % (y_min_body, y_max_body))
    logging.info ('body/mirrors width ratio = %.3f' % (width_body / width_mirrors))
    if width_body == width_mirrors:
        logging.warning ('mirror and body widths are equal: %.2f' % width_body)

    # form the result  (note origin.z=z_min)
    origin = [(x_min_body+x_max_body)/2, (y_min_body+y_max_body)/2, z_min]
    origin = dict(zip(['x', 'y', 'z'], origin))
    dims = [x_max_body-x_min_body, y_max_body-y_min_body, z_max-z_min]
    dims = dict(zip(['x', 'y', 'z'], dims))

    return origin, dims


def get_origin_and_dims_adjusted (car_group_name, min_count = 10):
    '''Run get_origin_and_dims with different parameters for adjusted result
    '''
    # first compensate for mirrors and save adjusted width
    for height_ratio in [0.1, 0.2, 0.33, 0.5, 0.7, 1]:
        try:
            logging.debug ('get_origin_and_dims_adjusted: trying %f' % height_ratio)
            _, dims = get_origin_and_dims (car_group_name, height_ratio, min_count)
            adjusted_width = dims['y']
            break
        except MinHeightException:
            logging.debug ('height_ratio %f failed' % height_ratio)

    # then do not compensate for anything for correct length and height
    origin, dims = get_origin_and_dims (car_group_name, height_ratio = 1,
                                        min_count = min_count)
    dims['y'] = adjusted_width
    return origin, dims


def get_origin_and_dims_single (car_group_name, mirrors=False):
    '''
    Args:
      mirrors:   if True, adjust 'y' for mirrors
    '''

    obj = bpy.data.groups[car_group_name].objects[0]
    roi = bounds(obj)
    origin = [(roi.x.min+roi.x.max)/2, (roi.y.min+roi.y.max)/2, roi.z.min]
    origin = dict(zip(['x', 'y', 'z'], origin))
    dims = [roi.x.max-roi.x.min, roi.y.max-roi.y.min, roi.z.max-roi.z.min]
    dims = dict(zip(['x', 'y', 'z'], dims))
    if mirrors:
        dims['y'] *= 0.87
    return origin, dims
    


def process_car_obj (scene_path, vehicle, dims_true):
    '''Rewrites all .obj models as .blend files. 
    The model will consist of many, many parts, and be all in one group
    Returns:
      nothing
    '''
    # start with assuming the bad
    vehicle['valid'] = False
    vehicle['ready'] = False

    model_id = vehicle['model_id']
    logging.info ('processing model: %s' % model_id)

    # start with an empty file
    bpy.ops.wm.open_mainfile(filepath=scene_path)

    try:
        obj_path = atcity(model['src_obj_file'])
        import_car_obj(obj_path, car_group_name=model_id)
    except:
        logging.error('could not open .obj file')
        vehicle['error'] = 'blender cannot open .obj file'
        return

    # rotate model 90 degrees if necessary
    try:
        origin, dims = get_origin_and_dims (model_id, height_ratio = 1)
    except Exception as e:
        logging.error (str(e))
        vehicle['error'] = str(e)
        return
    if dims['x'] < dims['y']:
        logging.info ('will rotate: x=%.2f < y=%.2f' % (dims['x'], dims['y']))
        bpy.ops.transform.rotate (value=90*pi/180, axis=(0,0,1))
    else:
        logging.info ('will NOT rotate: x=%.2f > y=%.2f' % (dims['x'], dims['y']))

    # get the origin and dims. At this point model is oriented along X
    origin, dims = get_origin_and_dims_adjusted (model_id)
    logging.info ('model width: %.2f' % dims['y'])

    # we don't need model parts anymore (they were used in get_origin_and_dims)
    obj = join_car_meshes (model_id)
    obj.select = True

    # set model origin to center(x,y) and z_min, and center model
    bpy.context.scene.cursor_location = (origin['x'], origin['y'], origin['z'])
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    obj.location = (0, 0, 0)

    # scale the model, according to the width
    scale = dims_true['y'] / dims['y']
    logging.info ('true width: %.2f, scale: %f' % (dims_true['y'], scale))
    bpy.ops.transform.resize (value=(scale, scale, scale))
    # scale dims and round to cm for json output
    dims.update((x, round(y * scale, 2)) for x, y in dims.items())
    vehicle['dims'] = dims

    # make all materials recieve ambient light
    for m in obj.material_slots:
        m.material.ambient = 1.0

    vehicle['valid'] = True
    vehicle['ready'] = True



def process_car_blend (scene_path, vehicle, dims_true):
    '''Rewrites all .obj models as .blend files. 
    The model will consist of many, many parts, and be all in one group
    Returns:
      nothing
    '''
    # start with assuming the bad
    vehicle['valid'] = False
    vehicle['ready'] = False

    model_id = vehicle['model_id']
    logging.info ('processing model: %s' % model_id)

    # start with an empty file
    bpy.ops.wm.open_mainfile(filepath=scene_path)


    try:
        import_blend_car (atcity(model['src_blend_file']), model_id)
    except:
        logging.error('could not import .blend model')
        vehicle['error'] = 'blender cannot import .blend model'
        return

    # select the car as object
    obj = bpy.data.objects[model_id]
    obj.select = True

    # create a group with the same name to match .obj import 
    car_group = bpy.data.groups.new(model_id)
    bpy.context.scene.objects.active = obj
    bpy.ops.object.group_link (group=model_id)

    # rotate model 90 degrees if necessary
    try:
        origin, dims = get_origin_and_dims_single (model_id)
    except Exception as e:
        logging.error (str(e))
        vehicle['error'] = str(e)
        return
    if dims['x'] < dims['y']:
        logging.info ('will rotate: x=%.2f < y=%.2f' % (dims['x'], dims['y']))
        logging.debug ('dims/origin before rotation: %s, %s' % (str(dims), str(origin)))
        bpy.context.scene.objects.active = bpy.context.scene.objects[model_id]
        bpy.ops.transform.rotate (value=90*pi/180, axis=(0,0,1))
    else:
        logging.info ('will NOT rotate: x=%.2f > y=%.2f' % (dims['x'], dims['y']))

    # get the origin and dims. At this point model is oriented along X
    origin, dims = get_origin_and_dims_single (model_id, mirrors=True)
    logging.debug ('dims/origin before moving: %s, %s' % (str(dims), str(origin)))

    # set model origin to center(x,y) and z_min, and center model
    bpy.context.scene.cursor_location = (origin['x'], origin['y'], origin['z'])
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    obj.location = (0, 0, 0)

    # # scale the model, according to the width
    # scale = dims_true['y'] / dims['y']
    # logging.info ('true width: %.2f, scale: %f' % (dims_true['y'], scale))
    # bpy.ops.transform.resize (value=(scale, scale, scale))
    # # scale dims and round to cm for json output
    # dims.update((x, round(y * scale, 2)) for x, y in dims.items())

    # print dims
    origin, dims = get_origin_and_dims_single (model_id, mirrors=True)
    logging.debug ('dims/origin final: %s, %s' % (str(dims), str(origin)))

    # make all materials recieve ambient light
    for m in obj.material_slots:
        m.material.ambient = 1.0

    vehicle['dims'] = dims
    vehicle['valid'] = True
    vehicle['ready'] = True



def process_model (scene_path, model):
    '''Rewrite the .blend file and change provided model dict
    Returns:
      nothing but changes 'model'
    '''
    valid = model['valid'] if 'valid' in model else True
    if not valid: 
        logging.info ('skip invalid model %s' % model['model_id'])
        return

    # if 'dims_true' in model:
    #     dims_true = model['dims_true']
    # else:
    #     # defaults for each model type
    #     assert model['vehicle_type'] in width_true, \
    #         'no default size for model type %s' % model['vehicle_type']
    #     dims_true = {'y': width_true[model['vehicle_type']]}
    # logging.info ('will use true dims: %s' % str(dims_true))

    if 'src_blend_file' in model:
        process_car_blend (scene_path, model, dims_true=None)
    elif 'src_obj_file' in model:
        process_car_obj   (scene_path, model, dims_true=None)
    else:
        raise Exception('not supported')

    # save clean blend
    dst_blend_file = op.join('data', model['dst_blend_file'])
    if not op.exists(atcity(op.dirname(dst_blend_file))):
        os.makedirs(atcity(op.dirname(dst_blend_file)))
    logging.info ('writing model to %s' % dst_blend_file)
    bpy.ops.wm.save_as_mainfile(filepath=atcity(dst_blend_file))

    # scale the DimsPlane to illustrate dimensions
    plane = bpy.data.objects['DimsPlane']
    plane.location = [0, 0, 0]
    plane.scale.x = model['dims']['x'] * 0.5
    plane.scale.y = model['dims']['y'] * 0.5

    # save a rendered example
    example_file = op.join('data', model['example_file'])
    if not op.exists(atcity(op.dirname(example_file))): 
        os.makedirs(atcity(op.dirname(example_file)))
    logging.info ('writing example to %s' % example_file)
    render_scene(atcity(example_file))




setupLogging('log/augmentation/cleanCollectionBlender.log', logging.DEBUG, 'a')

scene_path = atcity('data/augmentation/scenes/empty-import.blend')

src_model_path = op.join(WORK_DIR, 'model-src.json')
model = json.load(open(src_model_path))

process_model(scene_path, model)

dst_model_path = op.join(WORK_DIR, 'model-dst.json')
with open(dst_model_path, 'w') as f:
    f.write(json.dumps(model, indent=4))
