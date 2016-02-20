import sys, os, os.path as op
import argparse
import json
from processScene import process_video
from Video import Video
from Camera import Camera
from Cad import Cad
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
from helperSetup import setupLogging, atcity


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--logging_level', default=20, type=int)
    parser.add_argument('--use_example_background', action='store_true')
    parser.add_argument('--record_empty_frames', action='store_true')
    parser.add_argument('--frame_range', default='[::]', 
                        help='python style ranges, e.g. "[5::2]"')
    parser.add_argument('--job_file')
    args = parser.parse_args()

    setupLogging('log/augmentation/ProcessVideo.log', args.logging_level, 'w')

    job = json.load(open(atcity(args.job_file) ))
    process_video(job, args)
