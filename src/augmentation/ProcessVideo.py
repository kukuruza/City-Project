#!/usr/bin/env python
import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import argparse
import json
import logging
import multiprocessing
import traceback
from processScene import process_video, create_in_db
from Video import Video
from Camera import Camera
from Cad import Cad
from learning.helperSetup import setupLogging, atcity



def add_args_to_job(job, args):
    if 'frame_range' not in job:
        job['frame_range'] = args.frame_range
    if args.timeout:
        job['timeout'] = args.timeout
    job['no_annotations'] = args.no_annotations


def process_video_wrapper (job):
    try:
        process_video(job)
    except:
        logging.error('job for %s failed to process: %s' % \
                      (job['video_dir'], traceback.format_exc()))


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--logging_level', default=20, type=int)
    parser.add_argument('--timeout', type=int, 
                        help='maximum running time, in munutes')
    parser.add_argument('--no_annotations', action='store_true',
                        help='will speed up rendering since individual cars wont be rendered')
    parser.add_argument('--frame_range', default='[::]', 
                        help='python style ranges, e.g. "[5::2]"')
    parser.add_argument('--job_file')
    args = parser.parse_args()

    setupLogging('log/augmentation/ProcessVideo.log', args.logging_level, 'w')

    # depending on the number of jobs in the file, use one or many processes
    job_json = json.load(open(atcity(args.job_file) ))
    if isinstance(job_json, list):
        logging.info ('job file has multiple jobs. Will spin a process pool')
        jobs = job_json
        for i,job in enumerate(jobs): 
            add_args_to_job(jobs[i], args)
        pool = multiprocessing.Pool()
        logging.info ('the pool has %d workers' % pool._processes)
        pool.map (process_video_wrapper, jobs)
        pool.close()
        pool.join()
    else:
        logging.info ('job file has a single job')
        job = job_json
        #create_in_db(job)
        add_args_to_job(job, args)
        process_video(job)
