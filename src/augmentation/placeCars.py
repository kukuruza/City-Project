import sys, os, os.path as op
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import json
from math import cos, sin, pi, sqrt, pow
import numpy as np
import cv2
import string
import logging
import datetime
from numpy.random import normal, uniform, choice
from learning.helperSetup import atcity, setupLogging, setParamUnlessThere
from Cad import Cad
from Camera import Camera
from Video import Video

WORK_RENDER_DIR     = atcity('augmentation/blender/current-frame')
TRAFFIC_FILENAME  = 'traffic.json'


'''
Distribute cars across the map according to the lanes map and model collections
'''


def pick_random_vehicle (cad):
  '''returns a vehicle dictionary'''
  valid = False
  while not valid:
    collection = choice(cad._collections)
    vehicle = choice(collection['vehicles'])
    valid = vehicle['valid'] if 'valid' in vehicle else True
  return vehicle


def axes_png2blender (points, origin, pxls_in_meter):
    '''Change coordinate frame from pixel-based to blender-based (meters)
    Args:
      origin   - a dict with 'x' and 'y' fields, will be subtracted from each point
      pxls_in_meter - a scalar, must be looked up at the map image
    Returns:
      nothing
    '''
    assert points, 'there are no points'
    assert origin is not None and 'x' in origin and 'y' in origin, origin
    assert pxls_in_meter is not None
    for point in points:
        logging.debug ('axes_png2blender: before x,y = %f,%f' % (point['x'], point['y']))
        point['x'] = (point['x'] - origin['x']) / pxls_in_meter
        point['y'] = -(point['y'] - origin['y']) / pxls_in_meter
        logging.debug ('axes_png2blender: after  x,y = %f,%f' % (point['x'], point['y']))



class Lane:

  def __init__(self, name, lane_dict, mask, cad, intercar_m, speed_kph, pxls_in_meter):
    self.name = name

    self.N   = lane_dict['N']
    self.L_m = lane_dict['length'] / pxls_in_meter
    logging.debug('lane %s has length %.0f m' % (name, self.L_m))

    x        = lane_dict['x']
    y        = lane_dict['y']
    azimuth  = lane_dict['azimuth']
    self.points = [[x[i], y[i], azimuth[i]] for i in range(self.N)]

    if mask is not None:
      self.points = [p for p in self.points if not mask[p[1],p[0]]]
      self.N = len(self.points)

    self.step = 0
    self.vehicles = []
    self.cad = cad
    self.intercar_m = intercar_m
    self.speed_kph = speed_kph

    self.traffic_v_omega = np.random.lognormal(0.02, 0.01)
    logging.debug ('lane %s has traffic speed omega %.2f' % 
                    (name, self.traffic_v_omega))

    vehicle = pick_random_vehicle (self.cad)
    vehicle['n0'] = 0
    self.vehicles.append(vehicle)


  def update(self):
    '''Move all the cars, maybe start a new car, remove one if it jumps off
    The model for moving along the lane is:
      traffic_speed = sin(traffic_v_omega time)
      car_position += traffic_speed + sin(car_v_omega time) * intercar_dist/3
    '''

    # unit convertion
    AVG_FPS = 2.  # frame per second in NYC videos
    TPM = self.N / self.L_m
    speed_mps = self.speed_kph / 3.6
    speed_mpf = speed_mps / AVG_FPS
    speed_tpf = speed_mpf * TPM
    tr_speed_tpf = (1. + 0. * sin(self.traffic_v_omega * self.step)) * speed_tpf

    # # do we need to add another
    # if len(self.vehicles) == 0:
    #   need_new_car = True
    # elif self.vehicles[0]['n0'] / TPM > self.vehicles[0]['dims']['x'] + self.intercar_m:
    #   need_new_car = True
    # else:
    #   need_new_car = False
    # if need_new_car:
    #   vehicle = pick_random_vehicle (self.cad)
    #   vehicle['n0'] = 0.
    #   self.vehicles.append(vehicle)
    
    # # update all cars
    # for vehicle in self.vehicles:
    #   #vehicle['v'] = np.random.normal(loc=1.0, scale=SPEED_STD)
    #   vehicle['n0'] += 5#tr_speed_tpf
    #   n = vehicle['n0'] #+ sin(vehicle['car_V_omega'] * self.step) * self.intercar_m / 3

    #   # mark the vehicle for deletion if necessary
    #   if n > self.N:
    #     vehicle['to_delete'] = True
    #   else:
    #     point = self.points[int(n)]
    #     vehicle['x'] = point[0]
    #     vehicle['y'] = point[1]
    #     vehicle['azimuth'] = point[2]

    # # delete those vehicles that are marked
    # self.vehicles = [v for v in self.vehicles if not 'to_delete' in v]

    vehicle = self.vehicles[0]
    vehicle['n0'] += 5
    point = self.points[vehicle['n0']]
    vehicle['x'] = point[0]
    vehicle['y'] = point[1]
    vehicle['azimuth'] = point[2]
    

    self.step += 1


class TrafficModel:

  def __init__(self, camera, cad, intercar_m, speed_kph):

    self.camera = camera

    # load mask
    if 'mask' in camera:
      mask_path = atcity(op.join(camera['camera_dir'], camera['mask']))
      mask = cv2.imread (mask_path, cv2.IMREAD_GRAYSCALE)
      assert mask is not None, mask_path
      logging.info ('TrafficModel: loaded a mask')
    else:
      mask = None

    # create lanes
    lanes_path = atcity(op.join(camera['camera_dir'], camera['lanes_name']))
    lanes_dicts = json.load(open( lanes_path ))
    self.lanes = [Lane(('%d' % i), l, mask, cad, intercar_m, speed_kph, camera['pxls_in_meter']) 
                  for i,l in enumerate(lanes_dicts)]
    logging.info ('TrafficModel: loaded %d lanes' % len(self.lanes))


  def generate_map (self):
    ''' generate lanes map with cars for visualization '''

    width  = camera['map_dims']['width']
    height = camera['map_dims']['height']

    # generate maps
    img = np.zeros((height, width, 3), dtype=np.uint8)
    for lane in self.lanes:
      for i,point in enumerate(lane.points):
        img[point[1], point[0], 1] = 255
        # direction
        img[point[1], point[0], 2] = i * 255 / lane.N
        # azimuth
        img[point[1], point[0], 0] = point[2]
    img = cv2.cvtColor(img, cv2.COLOR_HSV2BGR)

    # put cars on top
    for lane in self.lanes:
      for v in lane.vehicles:
        cv2.circle(img, (v['x'],v['y']), 5, (128,128,128), -1)

    return img


  def get_next_frame(self, time):

    # update cars on each lane
    for lane in self.lanes:
      lane.update()

    # collect cars from all lanes
    vehicles = []
    for lane in self.lanes:
      vehicles += lane.vehicles

    # axes_png2blender (vehicles, self.camera['origin_image'], self.camera['pxls_in_meter'])

    # # figure out sun position based on the timestamp
    # sun = Sun()
    # sun_pose = sun.sun_poses [int(time.hour*60) + time.minute]
    # logging.info ('received timestamp: %s' % time)
    # logging.info ('calculated sunpose: %s' % str(sun_pose))

    # traffic = {'sun_altitude': sun_pose['altitude'], \
    #            'sun_azimuth':  sun_pose['azimuth'], \
    #            'weather':      video.info['weather'], \
    #            'vehicles':     vehicles
    #            }

    # return traffic
    


def sq(x): return pow(x,2)

def get_norm(x): return sqrt (sq(x['x']) + sq(x['y']) + sq(x['z']))

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
        azimuth = azimuth_map[y][x] * 2
        logging.debug ('put_random_vehicles x: %f, y: %f, azimuth: %f' % (x, y, azimuth))

        # car does not need to be in the lane center
        pos_std = 0.2   # meters away from the middle of the lane
        x += np.random.normal(0, pxl_in_meter * pos_std)
        y += np.random.normal(0, pxl_in_meter * pos_std)

        # keep choosing a car until find a valid one
        vehicle = pick_random_vehicle (cad)
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



class Sun:
  def __init__(self):
    sun_pose_file  = 'augmentation/resources/SunPosition-Jan13-09h.txt'

    # get sun angles. This is a hack for this particular video
    with open(atcity(sun_pose_file)) as f:
        sun_pos_lines = f.readlines()
    sun_pos_lines = sun_pos_lines[9:]
    self.sun_poses = []
    for line in sun_pos_lines:
        words = line.split()
        self.sun_poses.append({'altitude': float(words[2]), 'azimuth': float(words[3])})




def generate_current_frame (camera, video, cad, time, num_cars):
    ''' Generate traffic.json traffic file for a single frame
    '''
    pxl_in_meter   = camera['pxls_in_meter']

    # get the map of azimuths. 
    # it has gray values (r==g==b=) and alpha, saved as 4-channels
    azimuth_path = atcity(op.join(camera['camera_dir'], camera['azimuth_name']))
    azimuth_map = cv2.imread (azimuth_path, cv2.IMREAD_UNCHANGED)
    assert azimuth_map is not None and azimuth_map.shape[2] == 4

    # black out the invisible azimuth_map regions
    if 'mask' in camera and camera['mask']:
        mask_path = atcity(op.join(camera['camera_dir'], camera['mask']))
        mask = cv2.imread (mask_path, cv2.IMREAD_GRAYSCALE)
        assert mask is not None, mask_path
        azimuth_map[mask] = 0

    # choose vehicle positions
    vehicles = put_random_vehicles (azimuth_map, pxl_in_meter, cad, num_cars, 
                                    intercar_dist_mult=1.5)

    axes_png2blender (vehicles, camera['origin_image'], camera['pxls_in_meter'])

    # figure out sun position based on the timestamp
    sun = Sun()
    sun_pose = sun.sun_poses [int(time.hour*60) + time.minute]
    logging.info ('received timestamp: %s' % time)
    logging.info ('calculated sunpose: %s' % str(sun_pose))

    traffic = {'sun_altitude': sun_pose['altitude'], \
               'sun_azimuth':  sun_pose['azimuth'], \
               'vehicles': vehicles, \
               'weather': video.info['weather']}

    return traffic



if __name__ == "__main__":

  setupLogging ('log/augmentation/placeCars.log', logging.DEBUG, 'a')

  video_dir = 'augmentation/scenes/cam572/Jan13-10h'
  collection_names = ['7c7c2b02ad5108fe5f9082491d52810', 
                      'uecadcbca-a400-428d-9240-a331ac5014f6']
  timestamp = datetime.datetime.now()
  num_cars = 10
  video = Video(video_dir)
  camera = video.build_camera()

  cad = Cad()
  cad.load(collection_names)

  #traffic = generate_current_frame (video, collection_names, timestamp, num_cars)
  model = TrafficModel(camera, cad=cad, intercar_m=3, speed_kph=6)

  # cv2.imshow('lanesmap', model.generate_map())
  # cv2.waitKey(-1)
  while True:
    model.get_next_frame(timestamp)
    cv2.imshow('lanesmap', model.generate_map())
    key = cv2.waitKey(-1)
    if key == 27: break

  # traffic_path = op.join(WORK_RENDER_DIR, TRAFFIC_FILENAME)
  # with open(traffic_path, 'w') as f:
  #     f.write(json.dumps(traffic, indent=4))
