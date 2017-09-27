#! /usr/bin/env python2
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup import setupLogging, atcity
import numpy as np
import cv2

parser = argparse.ArgumentParser()
parser.add_argument('--in_npz_file', required=True)
parser.add_argument('--logging_level', default=20, type=int)
args = parser.parse_args()

setupLogging ('log/learning/synth2real/ShowNpz.log', args.logging_level, 'a')

array = np.load(atcity(args.in_npz_file))
patches = array['patches']
model_ids = array['model_ids'] if 'model_ids' in array else None

for patch in patches:
    cv2.imshow('test', patch)
    button = cv2.waitKey(-1)
    if button == 27: break

