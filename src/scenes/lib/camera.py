import sys, os, os.path as op
import shutil
import logging
import simplejson as json
from db.lib.helperSetup import atcity
from scipy.misc import imread, imsave
from glob import glob


class Camera:
  ''' Class knows about all the poses. '''

  def __init__ (self, camera_name):

    self.camera_name = camera_name
    self.camera_path = atcity(op.join('data/scenes', camera_name, 'camera.json'))
    assert op.exists(self.camera_path), self.camera_path
    logging.info ('Camera: loading info from: %s' % self.camera_path)
    self.info = json.load(open(self.camera_path))
    logging.debug(self.dump())

  def __getitem__(self, key):
      return self.info[key]

  def __contains__(self, key):
      return True if key in self.info else False

  def save(self, backup=True):
    if backup:
      backup_path = op.splitext(self.camera_path)[0] + '.backup.json'
      shutil.copyfile(self.camera_path, backup_path)
    with open(self.camera_path, 'w') as outfile:
      outfile.write(self.dump())

  def dump(self):
    mystr = json.dumps(self.info, sort_keys=True, indent=2)
    # TODO: write fancy H
    return mystr


class Pose(Camera):
  ''' Class for a specific pose. '''

  def __init__(self, camera_name, pose_id=0):
    Camera.__init__(self, camera_name)
    self.pose_id = pose_id

    assert 'poses' in self.info
    assert pose_id < len(self.info['poses']), pose_id
    logging.info ('Using pose_id %d' % pose_id)
    self.info['pose'] = self.info['poses'][pose_id]
    del self.info['poses']

    map_id = self.info['pose']['map_id'] if 'map_id' in self.info['pose'] else 0
    self.map_id = map_id
    assert map_id is not None and map_id < len(self.info['maps']), map_id
    self.info['map'] = self.info['maps'][map_id]
    del self.info['maps']

    logging.debug (self.dump())

  def get_pose_dir(self):
    return atcity(op.join('data/scenes', self.camera_name, 'pose%d' % self.pose_id))

  def get_map_dir(self):
    return atcity(op.join('data/scenes', self.camera_name, 'map%d' % self.map_id))

  def load_satellite(self):
    satellite_path = op.join(self.get_map_dir(), 'satellite.jpg')
    assert op.exists(satellite_path), satellite_path
    return imread(satellite_path)

  def load_frame(self):
    frame_pattern = op.join(self.get_pose_dir(), 'example*.jpg')
    frame_paths = glob(frame_pattern)
    assert len(frame_paths) > 0, frame_pattern
    frame_path = frame_paths[0]  # Take a single frame.
    return imread(frame_path)


if __name__ == "__main__":
    camera = Camera(camera_name='253')
