import json
import sys, os, os.path as op
import argparse
import logging
import collections
import time
from math import cos, sin, pi, sqrt

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/augmentation'))
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
from helperSetup import setupLogging, _setupCopyDb_  # untended use of _setupCopyDb_
import common



width_true = {'truck': 2.5, 'van': 2.2, 'taxi': 1.9, 
              'sedan': 1.9, 'bus': 2.5, 'schoolbus': 2.5}


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



def get_origin_and_dims (car_group_name, height_ratio = 0.33):
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
    Min_count_below_height_ratio = 10
    if count_below_height_ratio < Min_count_below_height_ratio:
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


def get_origin_and_dims_adjusted (car_group_name):
    '''Run get_origin_and_dims with different parameters for adjusted result
    '''
    # first compensate for mirrors and save adjusted width
    for height_ratio in [0.1, 0.2, 0.33, 0.5, 0.7, 1]:
        try:
            logging.debug ('get_origin_and_dims_adjusted: trying %f' % height_ratio)
            _, dims = get_origin_and_dims (car_group_name, height_ratio)
            adjusted_width = dims['y']
            break
        except MinHeightException:
            logging.debug ('height_ratio %f failed' % height_ratio)

    # then do not compensate for anything for correct length and height
    origin, dims = get_origin_and_dims (car_group_name, height_ratio = 1)
    dims['y'] = adjusted_width
    return origin, dims
    


def process_car (scene_path, collection_dir, vehicle, dims_true):
    '''Rewrites all .obj models as .blend files. 
    The model will consist of many, many parts, and be all in one group
    Returns:
      nothing
    '''
    model_id = vehicle['model_id']
    logging.info ('processing model: %s' % model_id)

    obj_path   = op.join(collection_dir, 'obj', '%s.obj' % model_id)
    blend_path = op.join(collection_dir, 'blend', '%s.blend' % model_id)
    jpg_path   = op.join(collection_dir, 'examples', '%s.png' % model_id)

    # start with an empty file
    bpy.ops.wm.open_mainfile(filepath=scene_path)

    try:
        common.import_car_obj(obj_path, car_group_name=model_id)
    except:
        logging.error('could not open .obj file')
        vehicle['valid'] = False
        vehicle['error'] = 'blender cannot open .obj file'
        return

    # rotate model 90 degrees if necessary
    try:
        origin, dims = get_origin_and_dims (model_id, height_ratio = 1)
    except Exception as e:
        logging.error (str(e))
        vehicle['valid'] = False
        vehicle['error'] = str(e)
        return
    if dims['x'] < dims['y']:
        bpy.ops.transform.rotate (value=90*pi/180, axis=(0,0,1))
        logging.info ('will rotate: x=%.2f < y=%.2f' % (dims['x'], dims['y']))
    else:
        logging.info ('will NOT rotate: x=%.2f > y=%.2f' % (dims['x'], dims['y']))

    # get the origin and dims. At this point model is oriented along X
    origin, dims = get_origin_and_dims_adjusted (model_id)
    logging.info ('model width: %.2f' % dims['y'])

    # we don't need model parts anymore (they were used in get_origin_and_dims)
    obj = common.join_car_meshes (model_id)
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

    # save a rendered image
    common.render_scene(jpg_path)

    bpy.ops.wm.save_as_mainfile(filepath=blend_path)

    #bpy.ops.object.delete()
    vehicle['valid'] = True






def process_collection (collection_dir, scene_path):

    collection_old_path = op.join(collection_dir, 'readme-src.json')
    collection_new_path = op.join(collection_dir, 'readme-blended.json')
    # back up collection json
    _setupCopyDb_ (collection_old_path, collection_new_path)
    collection = json.load(open(collection_old_path))

    if not op.exists (op.join(collection_dir, 'blend')):
        os.makedirs (op.join(collection_dir, 'blend'))
    if not op.exists (op.join(collection_dir, 'examples')):
        os.makedirs (op.join(collection_dir, 'examples'))

    for i,vehicle in enumerate(collection['vehicles']):
        valid = vehicle['valid'] if 'valid' in vehicle else True
        if not valid: 
            logging.debug ('skip invalid midel %s' % vehicle['model_id'])
            continue

        if 'dims_true' in vehicle:
            dims_true = vehicle['dims_true']
        else:
            # defaults for each vehicle type
            dims_true = {'y': width_true[vehicle['vehicle_type']]}
        logging.info ('will use true dims: %s' % str(dims_true))

        process_car (scene_path, collection_dir, vehicle, dims_true)

        # update collection
        collection['vehicles'][i] = vehicle

    # rewrite the collection
    with open(collection_new_path, 'w') as f:
        f.write(json.dumps(collection, indent=4))



#if __name__ == "__main__":
#
#    parser = argparse.ArgumentParser()
#    parser.add_argument('--collection_path')
#    parser.add_argument('--scale')
#    args = parser.parse_args()
#
#    scaleCollection (args.collection_path, args.scale)

scene_path = op.join(os.getenv('CITY_DATA_PATH'), 'augmentation/scenes/empty-import.blend')

collection_dir = op.join(os.getenv('CITY_DATA_PATH'), 
    'augmentation/CAD/taxi-without-collection')

setupLogging('log/augmentation/Obj2Blend.log', logging.DEBUG, 'w')

process_collection (collection_dir, scene_path)
