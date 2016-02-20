import sys, os, os.path as op
import argparse
from processScene import process_frame
from Video import Video
from Camera import Camera
from Cad import Cad
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
from helperSetup import setupLogging, atcity


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--no_traffic', action='store_true')
    parser.add_argument('--no_render',  action='store_true')
    parser.add_argument('--no_combine', action='store_true')
    parser.add_argument('--scale', default=1, type=float)  # why all cars are too big?
    parser.add_argument('--logging_level', default=20, type=int)
    parser.add_argument('--video_dir')
    parser.add_argument('--num_cars', default=10, type=int)
    parser.add_argument('--collection_names', nargs='+', 
                        default=['7c7c2b02ad5108fe5f9082491d52810'])
    args = parser.parse_args()

    setupLogging('log/augmentation/ProcessFrame.log', args.logging_level, 'w')

    video = Video(video_dir=args.video_dir)
    camera = video.build_camera()
    cad = Cad()
    cad.load(args.collection_names)

    background = video.example_background
    time = video.start_time
    num_cars = args.num_cars
    params = {'no_combine': args.no_combine,
              'no_render':  args.no_render,
              'no_traffic': args.no_traffic}

    process_frame (video, camera, cad, time, 
                   num_cars, background, scale=args.scale, params)

