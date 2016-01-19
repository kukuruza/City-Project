import os, os.path as op
import sys
import json
from math import cos, sin, pi, sqrt, pow
import numpy as np
import cv2
import string
import logging
import datetime
from numpy.random import normal, uniform, choice
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
from helperSetup import atcity, setupLogging

def sq(x): return pow(x,2)

'''
Distribute cars across the map according to the lanes map
'''

def put_random_points (azimuth_map, num, lane_width_pxl, min_intercar_dist_pxl):
    '''Picks a number of random point in the lane map.
    Args:
      azimuth_map - a color array (all values are gray) with alpha mask, [YxXx4]
      num     - a number of points to pick
    Returns:
      points  - a list of dictionaries, each has x,y,azimuth attributes
    '''
    # make azimuth_map a 2D array
    alpha, azimuth_map = azimuth_map[:,:,-1], azimuth_map[:,:,0]

    # get indices of all points which are non-zero
    Ps = np.transpose(np.nonzero(alpha))
    print 'total lane points:', Ps.shape

    # pick random points
    ind = np.random.choice (Ps.shape[0], size=num, replace=True)

    # get angles (each azimuth is multiplied by 2 by convention)
    points = []
    for P in Ps[ind]:
        x = P[1]
        y = P[0]
        azimuth = azimuth_map[P[0]][P[1]] * 2

        # cars can't be too close. TODO: they can be close on different lanes
        too_close = False
        for p in points:
            if sqrt(sq(p['y']-y) + sq(p['x']-x)) < min_intercar_dist_pxl:
                too_close = True
        if too_close: 
            continue
        
        # car does not need to be in the lane center
        x += np.random.normal(0, lane_width_pxl / 20)
        y += np.random.normal(0, lane_width_pxl / 20)
        
        points.append({'x': x, 'y': y, 'azimuth': azimuth})

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
      points - a list of dictionaries, each has x,y,azimuth attributes
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




collection_dir = 'augmentation/CAD/7c7c2b02ad5108fe5f9082491d52810'
sun_pose_file  = 'augmentation/resources/SunPosition-Jan13-09h.txt'

# get sun angles. This is a hack for this particular video
with open(atcity(sun_pose_file)) as f:
    sun_pos_lines = f.readlines()
sun_pos_lines = sun_pos_lines[9:]
sun_poses = []
for line in sun_pos_lines:
    words = line.split()
    sun_poses.append({'altitude': float(words[2]), 'azimuth': float(words[3])})




def generate_current_frame (camera_file, i_googlemap, timestamp, num_cars, weather):
    ''' Generate current-frame/traffic.json traffic file for a single frame
    '''
    # get azimuth map path
    camera_info    = json.load(open( atcity(camera_file) ))
    googlemap_info = camera_info['google_maps'][i_googlemap]

    # read the json file with cars data
    collection_path = atcity(op.join(collection_dir, '_collection_.json'))
    collection_info = json.load(open(collection_path))

    # get the map of azimuths. 
    # it has gray values (r==g==b=) and alpha, saved as 4-channels
    azimuth_map = cv2.imread (atcity(googlemap_info['azimuth_path']), cv2.IMREAD_UNCHANGED)
    assert azimuth_map is not None and azimuth_map.shape[2] == 4

    # choose vehicle positions
    points = put_random_points (azimuth_map, 
                                num=num_cars, 
                                lane_width_pxl=50, 
                                min_intercar_dist_pxl=50 * 4)

    axes_png2blender (points, googlemap_info['camera_origin'], 
                              googlemap_info['pxls_in_meter'])

    # choose models from collection
    pick_vehicles (points, collection_info)

    # figure out sun position based on the timestamp
    sun_pose = sun_poses [int(timestamp.hour*60) + timestamp.minute]
    logging.info ('received timestamp: %s' % timestamp)
    logging.info ('calculated sunpose: %s' % str(sun_pose))

    frame_info = { 'sun_altitude': sun_pose['altitude'], \
                   'sun_azimuth':  sun_pose['azimuth'], \
                   'vehicles': points, \
                   'weather': weather }

    with open(atcity( 'augmentation/render/current-frame/traffic.json' ), 'w') as f:
        f.write(json.dumps(frame_info, indent=4))



if __name__ == "__main__":

    setupLogging('log/augmentation/placeCars.log', logging.INFO, 'a')

    camera_file    = 'camdata/cam717/readme.json'
    i_googlemap    = 0
    num_cars       = 10
    weather        = ['Dry', 'Sunny']

    generate_current_frame (camera_file, i_googlemap, datetime.datetime.now(), num_cars, weather)
