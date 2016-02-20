import sys, os, os.path as op
from glob import glob
from datetime import datetime
import logging
import json
import cv2
import argparse
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
from Camera import Camera
from helperSetup import setupLogging, atcity

VIDEO_DIR_REGEX     = r'^[A-Z][a-z].*[0-9]{2}-[0-9]{2}h$'
VIDEO_DIR_STRPTIME  = '%b%d-%Hh'
TIME_FORMAT         = '%Y-%m-%d %H:%M:%S.%f'

class Video:

    def __init__ (self, video_dir=None, video_info=None):
        
        if video_dir:
            video_name = op.basename(video_dir)
            video_path = atcity(op.join(video_dir, '%s.json' % video_name))
            assert op.exists(video_path), video_path
            logging.info ('Video: loading info from: %s' % video_path)
            video_info = json.load(open(video_path))
        elif video_info:
            assert 'video_dir' in video_info
            video_dir = video_info['video_dir']
            assert op.exists(atcity(video_dir)), video_dir
            video_name = op.basename(video_dir)
        else:
            raise Exception ('pass video_info or video_dir')
        logging.info ('Video: parse info for: %s' % video_dir)

        assert 'weather' in video_info
        self.weather = video_info['weather']

        if 'example_frame_name' in video_info:
            logging.info ('- found example_frame_name: %s' % example_frame_name)
            self.example_frame = cv2.imread(op.join(video_dir, example_frame_name))
            assert self.example_frame is not None
        else:
            # trying possible paths, and take the first to match
            example_frame_paths = glob (atcity(op.join(video_dir, 'frame*.png')))
            if len(example_frame_paths) > 0:
                logging.info ('- deduced example_frame: %s' % example_frame_paths[0])
                self.example_frame = cv2.imread(example_frame_paths[0])
                assert self.example_frame is not None
            else:
                logging.warning ('- no example_frame for %s' % video_dir)
                self.example_frame = None

        if 'example_background_name' in video_info:
            logging.info ('- found example_background_name: %s' % example_background_name)
            self.example_background = cv2.imread(op.join(video_dir, example_background_name))
            assert self.example_background is not None
        else:
            # trying possible paths
            example_back_paths = glob (atcity(op.join(video_dir, 'background*.png')))
            if len(example_back_paths) > 0:
                logging.info ('- deduced example_background: %s' % example_back_paths[0])
                self.example_background = cv2.imread(example_back_paths[0])
                assert self.example_background is not None
            else:
                logging.warning ('- no example_background for %s' % video_dir)
                self.example_background = None

        if 'start_timestamp' in video_info:
            start_timestamp = video_info['start_timestamp']
            logging.info ('- found start_timestamp: %s' % start_timestamp)
            self.start_time = datetime.strptime(start_timestamp, TIME_FORMAT)
        else:
            # deduce from the name of the file
            self.start_time = datetime.strptime(video_name, VIDEO_DIR_STRPTIME)
            logging.info ('- deduced start_time: %s' % self.start_time.strftime(TIME_FORMAT))

        if 'video_file' in video_info:
            self.video_file = video_info['video_file']
            logging.info ('- found video_file: %s' % self.video_file)
        else:
            # deduce from the name of the file
            cam_dir = op.dirname(video_dir)
            self.video_file = op.join('camdata', op.basename(cam_dir), '%s.avi' % video_name)
            logging.info ('- deduced video_file: %s' % self.video_file)
            assert op.exists(atcity(self.video_file)), self.video_file

        if 'render_blend_file' in video_info:
            self.render_blend_file = video_info['render_blend_file']
            logging.info ('- found render_blend_file: %s' % self.render_blend_file)
            op.exists(atcity(self.render_blend_file))
        elif op.exists(atcity(op.join(video_dir, 'render.blend'))):
            # if found the default name in the video folder
            self.render_blend_file = op.join(video_dir, 'render.blend')
            logging.info ('- found render_blend_file in video dir: %s' % self.render_blend_file)
        else:
            logging.warning ('- could not figure out render_blend_file')

        if 'combine_blend_file' in video_info:
            self.combine_blend_file = video_info['combine_blend_file']
            logging.info ('- found combine_blend_file: %s' % self.combine_blend_file)
            op.exists(atcity(self.combine_blend_file))
        elif op.exists(atcity(op.join(video_dir, 'combine.blend'))):
            # if found the default name in the video folder
            self.combine_blend_file = op.join(video_dir, 'combine.blend')
            logging.info ('- found combine_blend_file in video dir: %s' % self.combine_blend_file)
        else:
            logging.warning ('- could not figure out combine_blend_file')

        if 'camera_dir' in video_info:
            self.camera_dir = video_info['camera_dir']
            logging.info ('- found camera_dir: %s' % self.camera_dir)
        else:
            # deduce from the name of the file
            self.camera_dir = op.dirname(video_dir)
            logging.info ('- deduced camera_dir: %s' % self.camera_dir)
        assert op.exists(atcity(self.camera_dir)), atcity(self.camera_dir)

        if 'pose_id' in video_info:
            self.pose_id = int(video_info['pose_id'])
            logging.info ('- found pose_id: %d' % self.pose_id)
        else:
            self.pose_id = 0
            logging.info ('- take default pose_id = 0')


    def build_camera (self):
        return Camera (camera_dir=self.camera_dir, pose_id=self.pose_id)

         

if __name__ == "__main__":

    setupLogging ('log/augmentation/Video.log', logging.DEBUG, 'w')

    video = Video(video_dir='augmentation/scenes/cam578/Mar15-10h')
    camera = video.build_camera()

    #video_file = 'augmentation/scenes/cam578/Mar15-10h/Mar15-10h.json'
    #video_info = json.load(open(atcity(video_file)))
    #video_info['video_dir'] = 'augmentation/scenes/cam578/Mar15-10h'
    #video.load(video_info=video_info)

    #assert video.example_background is not None
    #cv2.imshow('test', video.example_background)
    #cv2.waitKey(-1)


