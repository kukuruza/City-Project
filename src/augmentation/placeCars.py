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
from Cad import Cad

WORK_DIR = atcity('augmentation/blender/current-frame')


def sq(x): return pow(x,2)

def get_norm(x): return sqrt (sq(x['x']) + sq(x['y']) + sq(x['z']))

'''
Distribute cars across the map according to the lanes map and model collections
'''

def put_random_vehicles (azimuth_map, pxl_in_meter, cad, num, intercar_dist_mult):
    '''Places a number of random models to random points in the lane map.
    Args:
      azimuth_map:         a color array (all values are gray) with alpha mask, [YxXx4]
      pxl_in_meter:        for this particular map
      num:                 a number of vehicles to pick
      intercar_dist_mult:  cars won't be sampled closer than sum of their dims, 
                             multiplied by this factor
    Returns:
      vehicles:            a list of dictionaries, each has x,y,azimuth attributes
    '''
    # make azimuth_map a 2D array
    alpha, azimuth_map = azimuth_map[:,:,-1], azimuth_map[:,:,0]

    # get indices of all points which are non-zero
    Ps = np.transpose(np.nonzero(alpha))
    assert Ps.shape[0] > 0, 'azimuth_map is all zeros'

    # pick random points
    assert num > 0
    ind = np.random.choice (Ps.shape[0], size=num, replace=True)

    # get angles (each azimuth is multiplied by 2 by convention)
    dims_dict = {}
    vehicles = []
    for P in Ps[ind]:
        x = P[1]
        y = P[0]
        azimuth = azimuth_map[P[0]][P[1]] * 2
        logging.debug ('put_random_vehicles x: %f, y: %f, azimuth: %f' % (x, y, azimuth))

        # car does not need to be in the lane center
        pos_std = 0.2   # meters away from the middle of the lane
        x += np.random.normal(0, pxl_in_meter * pos_std)
        y += np.random.normal(0, pxl_in_meter * pos_std)

        # keep choosing a car until find a valid one
        valid = False
        while not valid:
            collection = choice(cad._collections)
            vehicle = choice(collection['vehicles'])
            valid = vehicle['valid'] if 'valid' in vehicle else True
        dims_dict[vehicle['model_id']] = vehicle['dims']

        # cars can't be too close. TODO: they can be close on different lanes
        too_close = False
        for vehicle2 in vehicles:

            # get the minimum idstance between cars in pixels
            car1_sz = get_norm(dims_dict[vehicle['model_id']])
            car2_sz = get_norm(dims_dict[vehicle2['model_id']])
            min_intercar_dist_pxl = intercar_dist_mult * pxl_in_meter * (car1_sz + car2_sz) / 2

            if sqrt(sq(vehicle2['y']-y) + sq(vehicle2['x']-x)) < min_intercar_dist_pxl:
                too_close = True
        if too_close: 
            continue
        
        vehicles.append({'x': x, 'y': y, 'azimuth': azimuth,
                         'collection_id': collection['collection_id'],
                         'model_id': vehicle['model_id']})

    print 'wrote %d vehicles' % len(vehicles)
    return vehicles



def axes_png2blender (points, origin, pxls_in_meter):
    '''Change coordinate frame from pixel-based to blender-based (meters)
    Args:
      origin   - a dict with 'x' and 'y' fields, will be subtracted from each point
      pxls_in_meter - a scalar, must be looked up at the map image
    Returns:
      nothing
    '''
    assert points, 'there are no points'
    assert origin is not None and type(origin) is dict
    assert pxls_in_meter is not None
    for point in points:
        logging.debug ('axes_png2blender: before x,y = %f,%f' % (point['x'], point['y']))
        point['x'] = (point['x'] - origin['x']) / pxls_in_meter
        point['y'] = -(point['y'] - origin['y']) / pxls_in_meter
        logging.debug ('axes_png2blender: after  x,y = %f,%f' % (point['x'], point['y']))



sun_pose_file  = 'augmentation/resources/SunPosition-Jan13-09h.txt'

# get sun angles. This is a hack for this particular video
with open(atcity(sun_pose_file)) as f:
    sun_pos_lines = f.readlines()
sun_pos_lines = sun_pos_lines[9:]
sun_poses = []
for line in sun_pos_lines:
    words = line.split()
    sun_poses.append({'altitude': float(words[2]), 'azimuth': float(words[3])})




def generate_current_frame (camera, video, cad, time, num_cars, scale=1):
    ''' Generate traffic.json traffic file for a single frame
    '''
    pxl_in_meter   = camera.info['pxls_in_meter']

    # get the map of azimuths. 
    # it has gray values (r==g==b=) and alpha, saved as 4-channels
    azimuth_path = atcity(op.join(camera.info['camera_dir'], camera.info['azimuth_name']))
    azimuth_map = cv2.imread (azimuth_path, cv2.IMREAD_UNCHANGED)
    assert azimuth_map is not None and azimuth_map.shape[2] == 4

    # black out the invisible azimuth_map regions
    if 'visible_area_name' in camera.info and camera.info['visible_area_name']:
        visibility_path = atcity(op.join(camera.info['camera_dir'], camera.info['visible_area_name']))
        visibility_map = cv2.imread (visibility_path, cv2.IMREAD_GRAYSCALE)
        assert visibility_map is not None
        azimuth_map[visibility_map] = 0

    # choose vehicle positions
    vehicles = put_random_vehicles (azimuth_map, pxl_in_meter, cad, num_cars, 
                                    intercar_dist_mult=1.5)

    axes_png2blender (vehicles, camera.info['origin_image'], camera.info['pxls_in_meter'])

    # figure out sun position based on the timestamp
    sun_pose = sun_poses [int(time.hour*60) + time.minute]
    logging.info ('received timestamp: %s' % time)
    logging.info ('calculated sunpose: %s' % str(sun_pose))

    frame_info = {'sun_altitude': sun_pose['altitude'], \
                  'sun_azimuth':  sun_pose['azimuth'], \
                  'vehicles': vehicles, \
                  'weather': video.weather,
                  'scale': scale }

    traffic_path = op.join(WORK_DIR, 'traffic.json')
    logging.debug ('traffic_path: %s' % traffic_path)
    with open(traffic_path, 'w') as f:
        f.write(json.dumps(frame_info, indent=4))



if __name__ == "__main__":

    setupLogging ('log/augmentation/placeCars.log', logging.DEBUG, 'a')

    video_info_file = 'augmentation/scenes/cam572/Jan13-10h/Jan13-10h.json'
    collection_names = ['7c7c2b02ad5108fe5f9082491d52810', 'uecadcbca-a400-428d-9240-a331ac5014f6']
    timestamp = datetime.datetime.now()
    num_cars = 10
    video_info = json.load(open( atcity(video_info_file) ))

    generate_current_frame (video_info, collection_names, timestamp, num_cars)
