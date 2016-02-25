import sys, os, os.path as op
import argparse
import json
import logging
from processScene import process_video
from Video import Video
from Camera import Camera
from Cad import Cad
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/backend'))
from video2dataset import make_back_dataset
from helperSetup import setupLogging, atcity


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--logging_level', default=20, type=int)
    parser.add_argument('--use_example_background', action='store_true')
    parser.add_argument('--record_empty_frames', action='store_true')
    parser.add_argument('--no_annotations', action='store_true',
                        help='will speed up rendering since individual cars wont be rendered')
    parser.add_argument('--frame_range', default='[::]', 
                        help='python style ranges, e.g. "[5::2]"')
    parser.add_argument('--job_file')
    args = parser.parse_args()

    setupLogging('log/augmentation/ProcessVideo.log', args.logging_level, 'w')

    job = json.load(open(atcity(args.job_file) ))

    # create a db first
    if 'in_db_file' not in job:
        assert 'video_dir' in job
        video_dir = job['video_dir']
        camera_name = op.basename(op.dirname(video_dir))
        video_name  = op.basename(video_dir)
        camdata_video_dir = op.join('camdata', camera_name, video_name)
        in_db_file = op.join('databases/augmentation', camera_name, video_name, 'back.db')
        if not op.exists(atcity(in_db_file)):
            make_back_dataset (camdata_video_dir, in_db_file)
        job['in_db_file'] = in_db_file
        logging.info ('created in_db_file from video: %s' % job['in_db_file'])        
    else:
        logging.info ('found in_db_file in job: %s' % job['in_db_file'])

    process_video(job, args)
