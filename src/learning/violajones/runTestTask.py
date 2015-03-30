import logging
import sys
import os, os.path as op
import shutil
import glob
import json
import random
import argparse
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
from setup_helper import setupLogging, get_CITY_DATA_PATH, setParamUnlessThere
from opencvInterface import loadJson, execCommand, ExperimentsBuilder


def test (experiment):
