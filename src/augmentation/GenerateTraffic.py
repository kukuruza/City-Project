#!/usr/bin/env python
import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import argparse
import json
import logging
from processScene import generate_video_traffic
from learning.helperSetup import setupLogging, atcity



def add_args_to_job(job, args):
    if 'frame_range' not in job:
        job['frame_range'] = args.frame_range


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--logging_level', default=20, type=int)
    parser.add_argument('--frame_range', default='[::]', 
                        help='python style ranges, e.g. "[5::2]"')
    parser.add_argument('--job_file', required=True)
    parser.add_argument('--traffic_file', required=True)
    args = parser.parse_args()

    setupLogging('log/augmentation/GenerateTraffic.log', args.logging_level, 'w')

    job = json.load(open(atcity(args.job_file) ))
    add_args_to_job(job, args)
    
    traffic = generate_video_traffic (job)

    with open(atcity(args.traffic_file), 'w') as f:
      f.write(json.dumps(traffic, indent=4))

