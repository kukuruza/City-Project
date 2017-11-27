import os, os.path as op
import shutil
import logging
import simplejson as json
from imageio import imread
#from scipy.misc import imread
from glob import glob

def _atcity(path):
  return op.join(os.getenv('CITY_PATH'), path)


class Info:
  def __init__(self):
    self.info = None
    self.path = None

  def __getitem__(self, key):
    return self.info[key]

  def __setitem__(self, key, item):
    self.info[key] = item

  def __contains__(self, key):
    return True if key in self.info else False

  def dump(self):
    mystr = json.dumps(self.info, sort_keys=True, indent=2)
    return mystr

  def load(self):
    assert op.exists(self.path), self.path
    logging.info ('%s: loading info from: %s' % (self.__class__.__name__, self.path))
    self.info = json.load(open(self.path))
    logging.debug(self.dump())

  def save(self, backup=True):
    if backup:
      backup_path = op.splitext(self.path)[0] + '.backup.json'
      shutil.copyfile(self.path, backup_path)
    with open(self.path, 'w') as outfile:
      outfile.write(self.dump())



class Camera(Info):
  def __init__ (self, camera_id):
    Info.__init__(self)
    self.camera_id = camera_id
    self.path = _atcity(op.join('data/scenes', camera_id, 'camera.json'))
    self.load()


class Map(Info):
  def __init__(self, camera_id, map_id):
    Info.__init__(self)
    self.camera_id = camera_id
    self.map_id = map_id
    self.path = op.join(self.get_map_dir(), 'map.json')
    self.load()

  def get_map_dir(self):
    return _atcity(op.join('data/scenes', self.camera_id, 'map%d' % self.map_id))

  def load_satellite(self):
    satellite_path = op.join(self.get_map_dir(), 'satellite.jpg')
    assert op.exists(satellite_path), satellite_path
    satellite = imread(satellite_path)
    assert satellite.shape[:2] == (self['map_dims']['height'], self['map_dims']['width'])
    return satellite


class Pose(Info):
  def __init__(self, camera_id, pose_id=0, map_id=None):
    '''
    Args: 
      map_id:  if set, use it instead of pose['best_map_id']
    '''
    Info.__init__(self)
    self.camera_id = camera_id
    self.pose_id = pose_id
    self.path = op.join(self.get_pose_dir(), 'pose.json')
    self.load()
    self.camera = Camera(self.camera_id)
    if map_id is not None:
      self.map_id = map_id
    elif 'best_map_id' in self:
      self.map_id = self['best_map_id']
    else:
      self.map_id = 0
    assert 'maps' in self, self.dump()
    assert self.map_id < len(self['maps']), self.map_id
    self.map = Map(self.camera_id, self.map_id)

  def get_pose_dir(self):
    return _atcity(op.join('data/scenes', self.camera_id, 'pose%d' % self.pose_id))

  def load(self):
    ''' Redefine load: if json is abscent, make default values. '''
    if not op.exists(self.path):
      self.info = {'best_map_id': 0, 'maps': [{ 'map_id': 0 }]}
      logging.debug(self.dump())
    else:
      Info.load(self)

  def save(self, backup=True):
    Info.save(self, backup=backup)
    self.camera.save(backup=backup)
    self.map.save(backup=backup)

  def load_frame(self):
    frame_pattern1 = op.join(self.get_pose_dir(), 'example*.*')
    frame_pattern2 = op.join(self.get_pose_dir(), 'frame*.*')
    frame_paths = glob(frame_pattern1) + glob(frame_pattern2)
    assert len(frame_paths) > 0, (frame_pattern1, frame_pattern2)
    frame_path = frame_paths[0]  # Take a single frame.
    frame = imread(frame_path)
    assert frame.shape[:2] == (
      self.camera['cam_dims']['height'], self.camera['cam_dims']['width'])
    return frame


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
  camera = Camera(camera_id='170')
  map = Map(camera_id='170', map_id=0)
  pose = Pose(camera_id='170', pose_id=1)

