import os, os.path as op
import sys
import json
from math import cos, sin, pi, sqrt, pow
import numpy as np
import cv2
import string
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
      yaw_map - a color array (all values are gray) with alpha mask, [YxXx4]
      num     - a number of points to pick
    Returns:
      points  - a list of dictionaries, each has x,y,yaw attributes
    '''
    # make yaw_map a 2D array
    alpha, yaw_map = yaw_map[:,:,-1], yaw_map[:,:,0]

    # get indices of all points which are non-zero
    Ps = np.transpose(np.nonzero(alpha))
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


def axes_png2blender (points, origin, pxls_in_meter):
    '''Change coordinate frame from pixel-based to blender-based (meters)
    Args:
      points - a list of dictionaries, each has x,y,yaw attributes
      origin - a dict with 'x' and 'y' fields, will be subtracted from each point
      pxls_in_meter - a scalar, must be looked up at the map image
    Returns:
      nothing
    '''
    assert origin is not None and type(origin) is dict
    assert pxls_in_meter is not None
    for point in points:
        point['x'] = (point['x'] - origin['x']) / pxls_in_meter
        point['y'] = -(point['y'] - origin['y']) / pxls_in_meter


def generate_frame_traffic (googlemap_info, collection_dir, number):

    # read the json file with cars data
    collection_path = atcity(op.join(collection_dir, '_collection_.json'))
    collection_info = json.load(open(collection_path))

    # get the map of yaws. 
    # it has gray values (r==g==b=) and alpha, saved as 4-channels
    yaw_map = cv2.imread (atcity(googlemap_info['yaw_path']), cv2.IMREAD_UNCHANGED)
    assert yaw_map is not None and yaw_map.shape[2] == 4

    points = put_random_points (yaw_map, num=number, lane_width_pxl=50, 
                                min_intercar_dist_pxl=50 * 2)

    axes_png2blender (points, googlemap_info['camera_origin'], 
                              googlemap_info['pxls_in_meter'])

    pick_vehicles (points, collection_info)

    weather = ['Dry', 'Cloudy']

    return {'vehicles': points, 'weather': weather}




camera_file    = 'camdata/cam572/readme.json'
collection_dir = 'augmentation/CAD/7c7c2b02ad5108fe5f9082491d52810'
num_cars       = 5
num_frames     = 100  # just need to be more than frames to use
out_file       = 'augmentation/traffic/traffic.json'
out_template   = 'augmentation/traffic/traffic-fr$.json'

# get yaw map path
camera_info    = json.load(open( atcity(camera_file) ))
googlemap_info = camera_info['google_maps'][1]

video_info = []
for i in range(num_frames):
    frame_info = generate_frame_traffic (googlemap_info, collection_dir, num_cars)
    video_info.append(frame_info)

with open(atcity(out_file), 'w') as f:
    f.write(json.dumps(video_info, indent=4))

# a workaround to call blender from bash once per frame
for i,frame_info in enumerate(video_info):
    with open(atcity( string.replace(out_template,'$','%06d'%i) ), 'w') as f:
        f.write(json.dumps(frame_info, indent=4))



