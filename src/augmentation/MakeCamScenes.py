import sys, os, os.path as op
from glob import glob
import json
import numpy as np
import cv2
import argparse
import logging
import subprocess
import shutil
import re
import traceback
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
from helperSetup import setupLogging, atcity
from ProcessScene import process_current_frame, jobParser

assert os.getenv('BLENDER_ROOT') is not None, \
    'export BLENDER_ROOT with path to blender binary as environmental variable'

WORK_SCENE_DIR      = atcity('augmentation/blender/current-scene')
WORK_RENDER_DIR     = atcity('augmentation/blender/current-frame')
EMPTY_SCENE_FILE    = 'augmentation/scenes/empty-render.blend'
SCENES_INFO_NAME    = 'scene.json'
EXAMPLE_DIRNAME     = 'examples'
NORMAL_FILENAME     = 'normal.png'
VIDEO_DIR_REGEX     = r'^[A-Z][a-z].*[0-9]{2}-[0-9]{2}h$'



def make_cam_scene (in_file, out_file):
    logging.info ('make_cam_scene in_file:  %s' % in_file)
    logging.info ('make_cam_scene out_file: %s' % out_file)

    # write a temporary file for blender
    scene_info = { 'in_file':  in_file, 'out_file': out_file }
    with open(op.join(WORK_SCENE_DIR, SCENES_INFO_NAME), 'w') as f:
        f.write(json.dumps(scene_info, indent=4))

    # create scene
    command = '%s/blender %s --background --python %s/src/augmentation/makeCamScene.py' % \
              (os.getenv('BLENDER_ROOT'), atcity(EMPTY_SCENE_FILE), os.getenv('CITY_PATH'))
    returncode = subprocess.call ([command], shell=True)
    logging.info ('blender returned code %s' % str(returncode))
    assert atcity(out_file), 'blender did not create out_file'



def _add_alpha_ (img):
    b_channel, g_channel, r_channel = cv2.split(img)
    alpha_channel = np.ones((img.shape[0], img.shape[1]), dtype=img.dtype) * 255
    return cv2.merge((b_channel, g_channel, r_channel, alpha_channel))


def add_example_to_rendered (rendered_path, video_info):
    '''Put rendered frame side by side with an example from video
    '''
    # load example frame
    example_frame_file = video_info['example_frame_file']
    logging.info ('add_example_to_rendered example_frame_file: %s' % example_frame_file)
    assert op.exists (atcity(example_frame_file)), '%s' % atcity(example_frame_file)
    example_frame = cv2.imread (atcity(example_frame_file))
    example_frame = _add_alpha_(example_frame)

    # load rendered image
    rendered = cv2.imread (rendered_path, -1)

    # put them side by side, and rewrite rendered file
    assert rendered.shape == example_frame.shape
    rendered = np.vstack ((rendered, example_frame))
    cv2.imwrite (rendered_path, rendered)



def render_example (out_file, video_info_file):
    logging.info ('render_example will render an example for %s' % video_info_file)

    # read video_info and replace render_blend_file
    video_info = json.load(open( atcity(video_info_file) ))
    video_info['render_blend_file'] = out_file

    # render a single frame
    timestamp = video_info['example_timestamp'] if 'example_timestamp' in video_info else None
    job = {'video_info': video_info,
           'num_cars': 20,
           'collections': [ "7c7c2b02ad5108fe5f9082491d52810" ],
           'timestamp': timestamp
          }
    args = jobParser.parse_args(['--no_combine'])
    process_current_frame (job, args)

    rendered_path = op.join(WORK_RENDER_DIR, NORMAL_FILENAME)
    assert op.exists(rendered_path), 'blender failed to render for this video' 

    add_example_to_rendered (rendered_path, video_info)



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    # switch for all cameras
    parser.add_argument('--all', action='store_true', help='all cameras')
    # input when just one camera
    parser.add_argument('--in_file')
    parser.add_argument('--out_file')
    parser.add_argument('--video_info_file', default='')
    # parameters
    parser.add_argument('--no_make_cam_scene', action='store_true', 
                        help='no useful work, use to debug render_example')
    parser.add_argument('--no_render_examples', action='store_true', 
                        help='render an example from [each] video')
    parser.add_argument('--logging_level', default=20, type=int)
    args = parser.parse_args()

    setupLogging('log/augmentation/MakeScenes.log', args.logging_level, 'w')

    if not args.all:
        if not args.no_make_cam_scene:
            make_cam_scene (args.in_file, args.out_file)
        if not args.no_render_examples:
            render_example (args.out_file, args.video_info_file)

    elif args.all:
        cam_dirs = glob(atcity('augmentation/scenes/cam*'))
        logging.info ('found %d cameras' % len(cam_dirs))
        for cam_dir in cam_dirs:

            cam_dir_name = op.basename(cam_dir)
            in_file  = op.join('augmentation/scenes', cam_dir_name, 'geometry.blend')
            out_file = op.join('augmentation/scenes', cam_dir_name, 'camera-render.blend')

            try:

                # make a camera scene
                if not args.no_make_cam_scene:
                    make_cam_scene (in_file, out_file)

                if args.no_render_examples:
                    continue

                # for each video, render an example
                subdirs = glob(op.join(cam_dir, '*'))
                subdirs = [x for x in subdirs if re.findall(VIDEO_DIR_REGEX, op.basename(x))]
                logging.info ('found %d video subdirs' % len(subdirs))

                for subdir in subdirs:
                    try:
                        video_dir_name = op.basename(subdir)
                        video_info_file = op.join('augmentation/scenes', cam_dir_name, 
                                             video_dir_name, '%s.json' % video_dir_name)
                        logging.info ('will render example for video %s' % video_info_file)
                        render_example (out_file, video_info_file)

                        # copy to examples folder
                        rendered_path = op.join(WORK_RENDER_DIR, NORMAL_FILENAME)
                        example_name = '%s-%s.png' % (cam_dir_name, video_dir_name)
                        example_path = op.join(WORK_SCENE_DIR, EXAMPLE_DIRNAME, example_name)
                        shutil.copyfile (rendered_path, example_path)
                    except:
                        logging.error('video not processed: %s' % traceback.format_exc())

            except:
                logging.error('camera not processed: %s' % traceback.format_exc())

