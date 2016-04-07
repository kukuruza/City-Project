#!/usr/bin/env python
import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import shutil
import argparse
from fnmatch import fnmatch
from random import shuffle
from learning.helperSetup import setupLogging, atcity


def _find_files(directory, pattern):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch(basename, pattern):
                filename = op.join(root, basename)
                yield filename


def copy_dir (in_base_dir, out_dir):

  if op.exists(atcity(out_dir)):
    shutil.rmtree(atcity(out_dir))
  os.makedirs(atcity(out_dir))

  i = 0
  for in_filepath in _find_files (atcity(in_base_dir), '*.jpg'):
    out_filepath = op.join (atcity(out_dir), '%08d.jpg' % i)
    shutil.copy (in_filepath, out_filepath)
    i += 1



if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  parser.add_argument('--in_base_dir')
  parser.add_argument('--out_dir')
  parser.add_argument('--logging_level', type=int, default=20)
  args = parser.parse_args()

  copy_dir(args.in_base_dir, args.out_dir)
