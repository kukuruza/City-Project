#!/usr/bin/env python
import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import json
import argparse
import logging
import subprocess
import shutil
import traceback
from learning.helperSetup import setupLogging, atcity
from learning.helperSetup import setParamUnlessThere, assertParamIsThere
from learning.helperKeys import KeyReaderUser, getCalibration
from augmentation.Cad import Cad


WORK_DIR = atcity('data/augmentation/blender/current-collection')


class Diapason:

  def _parse_range_str_ (self, range_str, length):
    '''Parses python range STRING into python range
    '''
    assert isinstance(range_str, basestring)
    # remove [ ] around the range
    if len(range_str) >= 2 and range_str[0] == '[' and range_str[-1] == ']':
      range_str = range_str[1:-1]
    # split into three elements start,end,step. Assign step=1 if missing
    arr = range_str.split(':')
    assert len(arr) == 2 or len(arr) == 3, 'need 1 or 2 commas "," in range string'
    if len(arr) == 2: arr.append('1')
    if arr[0] == '': arr[0] = '0'
    if arr[1] == '': arr[1] = str(length)
    if arr[2] == '': arr[2] = '1'
    start = int(arr[0])
    end   = int(arr[1])
    step  = int(arr[2])
    range_py = range(start, end, step)
    logging.debug ('Diapason parsed range_str %s into range of length %d' % (range_str, len(range_py)))
    return range_py

  def get_range (self, length, range_str):
    return self._parse_range_str_ (range_str, length)



def render_example (model):

  collection_id = model['collection_id']
  model_id      = model['model_id']

  collection_dir = 'data/augmentation/CAD/%s' % collection_id
  blend_file   = op.join(collection_dir, 'blend/%s.blend' % model_id)
  example_file = op.join(collection_dir, 'examples/%s.png' % model_id)
  model['blend_file']   = blend_file
  model['example_file'] = example_file

  if not op.exists(atcity(blend_file)):
    logging.info ('skipping non-existing %s' % blend_file)
    return

  model_path = op.join(WORK_DIR, 'model.json')
  with open(model_path, 'w') as f:
    f.write(json.dumps(model, indent=4))

  try:
    command = ['%s/blender' % os.getenv('BLENDER_ROOT'), '--background', '--python',
               atcity('src/augmentation/collections/renderExample.py')]
    returncode = subprocess.call (command, shell=False)
    logging.info ('blender returned code %s' % str(returncode))
  except:
    logging.error('failed: %s' % traceback.format_exc())
    return




parser = argparse.ArgumentParser()
parser.add_argument('--collection_id')
parser.add_argument('--model_range', default='[::]')
parser.add_argument('--logging_level', type=int, default=20)
args = parser.parse_args()

setupLogging('log/augmentation/RenderCollectionExamples.log', args.logging_level, 'w')

collection_file = 'data/augmentation/CAD/%s/collection.json' % args.collection_id
collection = json.load(open(atcity(collection_file)))

logging.info ('found %d models in the collection' % len(collection['vehicles']))

for i in Diapason().get_range(len(collection['vehicles']), args.model_range):
  logging.debug ('model #%d' % i)
  model = collection['vehicles'][i]
  model['collection_id'] = args.collection_id
  render_example (model)
