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
from processScene import process_frame
from Video import Video
from Camera import Camera
from Cad import Cad

assert os.getenv('BLENDER_ROOT') is not None, \
    'export BLENDER_ROOT with path to blender binary as environmental variable'

WORK_SCENE_DIR      = atcity('augmentation/blender/current-scene')
WORK_RENDER_DIR     = atcity('augmentation/blender/current-frame')
EMPTY_SCENE_FILE    = 'augmentation/scenes/empty-render.blend'
SCENES_INFO_NAME    = 'scene.json'
EXAMPLE_DIRNAME     = 'examples'
STACKED_FILENAME    = 'stacked.png'
VIDEO_DIR_REGEX     = r'^[A-Z][a-z].*[0-9]{2}-[0-9]{2}h$'



def make_render_scene (in_file, out_file, camera, video):
    logging.info ('make_render_scene in_file:  %s' % in_file)
    logging.info ('make_render_scene out_file: %s' % out_file)

    # write a temporary file for blender
    scene_info = { 'in_render_file':  in_file, 
                   'out_render_file': out_file, 
                   'camera_info':     camera.info }
    with open(op.join(WORK_SCENE_DIR, SCENES_INFO_NAME), 'w') as f:
        f.write(json.dumps(scene_info, indent=4))

    # create scene
    command = '%s/blender %s --background --python %s/src/augmentation/makeRenderScene.py' % \
              (os.getenv('BLENDER_ROOT'), atcity(EMPTY_SCENE_FILE), os.getenv('CITY_PATH'))
    returncode = subprocess.call ([command], shell=True)
    logging.info ('blender returned code %s' % str(returncode))
    assert atcity(out_file), 'blender did not create out_file'



def make_combine_scene (in_file, out_file, camera, video):
    logging.info ('make_combine_scene in_file:  %s' % in_file)
    logging.info ('make_combine_scene out_file: %s' % out_file)

    # write a temporary file for blender
    scene_info = { 'in_combine_file':  in_file, 
                   'out_combine_file': out_file, 
                   'camera_info': camera.info }
    with open(op.join(WORK_SCENE_DIR, SCENES_INFO_NAME), 'w') as f:
        f.write(json.dumps(scene_info, indent=4))

    # create scene
    command = '%s/blender %s --background --python %s/src/augmentation/makeCombineScene.py' % \
              (os.getenv('BLENDER_ROOT'), atcity(EMPTY_SCENE_FILE), os.getenv('CITY_PATH'))
    returncode = subprocess.call ([command], shell=True)
    logging.info ('blender returned code %s' % str(returncode))
    assert atcity(out_file), 'blender did not create out_file'



def render_example (out_render_file, out_combine_file, video_dir):
    logging.info ('render_example will render an example for %s' % video_dir)

    video = Video(video_dir=video_dir)
    video.render_blend_file = out_render_file
    video.combine_blend_file = out_combine_file
    camera = video.build_camera()
    background = video.example_background
    time = video.start_time

    cad = Cad()
    cad.load(['7c7c2b02ad5108fe5f9082491d52810'])
    num_cars = 20

    image, _ = process_frame (video, camera, cad, time, num_cars, background)
    assert image is not None
    
    stacked_path = op.join(WORK_RENDER_DIR, STACKED_FILENAME)
    add_example_to_rendered (image, video, stacked_path)



def add_example_to_rendered (rendered, video, stacked_path):
    '''Put rendered frame side by side with an example from video
    '''
    # load example frame
    example_frame = video.example_frame
    if example_frame is None: 
        raise Exception ('this video does not have example_frame')

    # put them side by side, and rewrite rendered file
    assert rendered.shape == example_frame.shape
    rendered = np.vstack ((rendered, example_frame))
    cv2.imwrite (stacked_path, rendered)








if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    # switch for all cameras
    parser.add_argument('--all', action='store_true', help='all cameras')
    # input when just one camera
    parser.add_argument('--in_render_file')
    parser.add_argument('--in_combine_file')
    parser.add_argument('--video_dir')
    # parameters
    parser.add_argument('--no_make_cam_scene', action='store_true', 
                        help='no useful work, use to debug render_example')
    parser.add_argument('--no_render_examples', action='store_true', 
                        help='render an example from [each] video')
    parser.add_argument('--logging_level', default=20, type=int)
    args = parser.parse_args()

    setupLogging('log/augmentation/MakeScenes.log', args.logging_level, 'w')

    if not args.all:
        # load camera and video info files
        video = Video(video_dir=args.video_dir)
        camera = video.build_camera()

        if not args.no_make_cam_scene:
            out_render_file = op.join(args.video_dir, 'render-generated.blend')
            make_render_scene (args.in_render_file, out_render_file, camera, video)
            out_combine_file = op.join(args.video_dir, 'combine-generated.blend')
            make_combine_scene (args.in_combine_file, out_combine_file, camera, video)
        if not args.no_render_examples:
            render_example (out_render_file, out_combine_file, args.video_dir)


    elif args.all:
        cam_dirs = glob(atcity('augmentation/scenes/cam*'))
        logging.info ('found %d cameras' % len(cam_dirs))
        for cam_dir in cam_dirs:

            # for each video, render an example
            subdirs = glob(op.join(cam_dir, '*'))
            subdirs = [x for x in subdirs if re.findall(VIDEO_DIR_REGEX, op.basename(x))]
            logging.info ('found %d video subdirs' % len(subdirs))

            for subdir in subdirs:

                cam_dir_name = op.basename(cam_dir)
                video_dir_name = op.basename(subdir)
                video_dir = op.join('augmentation/scenes', cam_dir_name, video_dir_name)

                try:
                    # load camera and video info files
                    video = Video(video_dir=video_dir)
                    camera = video.build_camera()

                    if not args.no_make_cam_scene:
                        in_file  = op.join('augmentation/scenes', cam_dir_name, 'geometry.blend')
                        out_render_file  = op.join(video_dir, 'render-generated.blend')
                        make_render_scene (in_file, out_render_file, camera, video)
                        in_file = op.join('augmentation/scenes/empty-combine.blend')
                        out_combine_file = op.join(video_dir, 'combine-generated.blend')
                        make_combine_scene (in_file, out_combine_file, camera, video)

                    if not args.no_render_examples:
                        render_example (out_render_file, out_combine_file, video_dir)

                        # copy to examples folder
                        stacked_path = op.join(WORK_RENDER_DIR, STACKED_FILENAME)
                        example_name = '%s-%s.png' % (cam_dir_name, video_dir_name)
                        example_path = op.join(WORK_SCENE_DIR, EXAMPLE_DIRNAME, example_name)
                        shutil.copyfile (stacked_path, example_path)

                except:
                    logging.error('video %s failed to process: %s' % \
                                  (video_dir, traceback.format_exc()))

