import os, os.path as op
import sys
import json
from math import cos, sin, pi, sqrt, pow
import numpy as np
import cv2
from numpy.random import normal, uniform, choice
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
from helperSetup import atcity

def sq(x): return pow(x,2)

'''
Distribute cars across the map according to the lanes map
'''

def put_random_points (yaw_map, num, lane_width_pxl, min_intercar_dist_pxl):
    '''Picks a number of random point in the lane map.
    Args:
      yaw_map - numpy 2D array with yaw marked as nonzeros
      num     - a number of points to pick
    Returns:
      points  - a list of dictionaries, each has x,y,yaw attributes
    '''
    # get indices of all points which are non-zero
    Ps = np.transpose(np.nonzero(yaw_map))
    print 'total lane points:', Ps.shape

    # pick random points
    ind = np.random.choice (Ps.shape[0], size=num, replace=True)

    # get angles (each yaw is multiplied by 2 by convention)
    points = []
    for P in Ps[ind]:
        x = P[1]
        y = P[0]
        yaw = yaw_map[P[0]][P[1]] * 2

        # cars can't be too close. TODO: they can be close on different lanes
        too_close = False
        for p in points:
            if sqrt(sq(p['y']-y) + sq(p['x']-x)) < min_intercar_dist_pxl:
                too_close = True
        if too_close: 
            continue
        
        # car does not need to be in the lane center
        x += np.random.normal(0, lane_width_pxl / 10)
        y += np.random.normal(0, lane_width_pxl / 10)
        
        points.append({'x': x, 'y': y, 'yaw': yaw})

    print 'wrote %d points' % len(points)
    return points


def pick_vehicles (points, vehicle_info):
    '''For each point pick a random vehicle from the list
    '''
    for point in points:
        valid = False
        # keep choosing a car until find a valid one
        while not valid: 
            vehicle = choice(vehicle_info['vehicles'])
            valid = vehicle['valid'] if 'valid' in vehicle else True
        point['collection_id'] = vehicle_info['collection_id']
        point['model_id'] = vehicle['model_id']
    return points



def axes_png2blender (points, origin_x, origin_y, dims_pixels, dims_meters):
    '''Change coordinate frame from pixel-based to blender-based (meters)
    Args:
      points - a list of dictionaries, each has x,y,yaw attributes
      origin_x, origin_y - will be subtracted from each point
      dims_pixels - (Y,X) shape of the map in pixels
      dims_meters - (Y,X) shape of the map in meters
    Returns:
      points - a new list
    '''
    coef_y = dims_meters[0] / dims_pixels[0]
    coef_x = dims_meters[1] / dims_pixels[1]

    for i,point in enumerate(points):
        points[i] = {'x':  (point['x'] - origin_x) * coef_x, 
                     'y': -(point['y'] - origin_y) * coef_y, 
                     'yaw': point['yaw']}
    return points


yaw_map_file   = 'models/cam572/googleAngles2.png'
collection_dir = 'augmentation/CAD/7c7c2b02ad5108fe5f9082491d52810'
traffic_file   = 'augmentation/traffic/traffic-572.json'

# read the json file with cars data
collection_path = atcity(op.join(collection_dir, '_collection_.json'))
collection_info = json.load(open(collection_path))

# TODO: change to black to transparent
yaw_map = cv2.imread (atcity(yaw_map_file))
assert yaw_map is not None and len(yaw_map.shape) == 3
yaw_map = yaw_map[:,:,2]  # red channel
assert yaw_map.max() > 0

points = put_random_points (yaw_map, num=12, lane_width_pxl=50, 
                            min_intercar_dist_pxl=50 * 2)

points = axes_png2blender (points, origin_x=443, origin_y=604, 
                           dims_pixels=yaw_map.shape, dims_meters=(64.00, 57.00))

points = pick_vehicles (points, collection_info)

weather = ['Dry', 'Cloudy']

json_str = json.dumps({'poses': points, 'weather': weather}, indent=4)
with open(atcity(traffic_file), 'w') as f:
    f.write(json_str)

