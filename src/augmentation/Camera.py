import sys, os, os.path as op
#from glob import glob
import logging
import json
#import cv2
#import argparse
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
from helperSetup import setupLogging, atcity


class Camera:

    def __init__ (self, camera_dir=None, info=None, pose_id=0):

        # get camera_info (dict) and camera_name
        if camera_dir:
            self.camera_name = op.basename(camera_dir)
            camera_path = atcity(op.join(camera_dir, '%s.json' % self.camera_name))
            assert op.exists(camera_path), camera_path
            logging.info ('Camera: loading info from: %s' % camera_path)
            self.info = json.load(open(camera_path))
            self.info['camera_dir'] = camera_dir
        elif info:
            assert 'camera_dir' in info
            self.info = info
            self.info['camera_dir'] = info['camera_dir']
            self.camera_name = op.dirname(info['camera_dir'])
        else:
            raise Exception ('pass camera_info or camera_dir')
        logging.info ('Camera: parse info for: %s' % self.camera_name)

        # read the proper camera_pose
        assert 'camera_poses' in self.info
        assert pose_id < len(self.info['camera_poses'])
        logging.info ('- using camera_pose %d' % pose_id)
        self.info.update(self.info['camera_poses'][pose_id])
        assert 'map_id' in self.info
        del self.info['camera_poses']

        # read te proper google_map
        assert 'google_maps' in self.info
        map_id = self.info['map_id']
        assert map_id < len(self.info['google_maps'])
        logging.info ('- using google_maps %d' % map_id)
        self.info.update(self.info['google_maps'][map_id])
        del self.info['google_maps']
        


if __name__ == "__main__":

    setupLogging ('log/augmentation/Video.log', logging.DEBUG, 'w')

    camera = Camera(camera_dir='augmentation/scenes/cam717')
    print json.dumps(camera.info, indent = 4)
