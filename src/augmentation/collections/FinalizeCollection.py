#!/usr/bin/env python
import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import simplejson as json
import argparse
import logging
import numpy as np
import subprocess
import traceback
from pprint import pprint, pformat
from learning.helperSetup import setupLogging, atcity, _setupCopyDb_

WORK_DIR = atcity('data/augmentation/blender/current-collection')




def get_dims (model):

  collection_id = model['collection_id']
  model_id      = model['model_id']

  collection_dir = 'data/augmentation/CAD/%s' % collection_id
  blend_file   = op.join(collection_dir, 'blend/%s.blend' % model_id)
  model['blend_file']   = blend_file

  if not op.exists(atcity(blend_file)):
    logging.info ('skipping non-existing %s' % blend_file)
    return

  model_path = op.join(WORK_DIR, 'model.json')
  with open(model_path, 'w') as f:
    f.write(json.dumps(model, indent=4))

  try:
    command = ['%s/blender' % os.getenv('BLENDER_ROOT'), '--background', '--python',
               atcity('src/augmentation/collections/getDims.py')]
    returncode = subprocess.call (command, shell=False)
    logging.info ('blender returned code %s' % str(returncode))
  except:
    logging.error('failed: %s' % traceback.format_exc())
    return

  model = json.load(open(model_path))
  return model['dims']



if __name__ == "__main__":

  parser = argparse.ArgumentParser('Make models invalid if no .blend file exists.')
  parser.add_argument('--collection_id', required=True)
  parser.add_argument('--logging_level', type=int, default=20)
  args = parser.parse_args()

  setupLogging('log/augmentation/ManuallyFilterCollection.log', args.logging_level, 'w')

  collection_file = 'data/augmentation/CAD/%s/collection.json' % args.collection_id
  #backup_file     = 'data/augmentation/CAD/%s/collection.json.backup' % args.collection_id
  #_setupCopyDb_ (atcity(collection_file), atcity(backup_file))

  collection = json.load(open(atcity(collection_file)))
  logging.info ('found %d models in the collection' % len(collection['vehicles']))

  for i in range(len(collection['vehicles'])):

    collection_id = collection['collection_id']
    collection_dir = 'data/augmentation/CAD/%s' % collection_id
    model = collection['vehicles'][i]

    blend_file   = op.join(collection_dir, 'blend/%s.blend' % model['model_id'])
    example_file = op.join(collection_dir, 'examples/%s.png' % model['model_id'])
    if not op.exists(atcity(blend_file)):
      collection['vehicles'][i]['valid'] = False
      if op.exists(atcity(example_file)):
        os.remove(atcity(example_file))
    if model['valid']:
      model['collection_id'] = collection_id
      collection['vehicles'][i]['dims'] = get_dims(model)
      collection['vehicles'][i]['ready'] = True
    if not model['valid']:
      if op.exists(atcity(blend_file)):
        logging.info ('removing invalid model %s' % blend_file)
        os.remove(atcity(blend_file))


  logging.info ('%d valid/ready models in the collection' % 
    sum(1 for x in collection['vehicles'] if x['valid']))

  with open(atcity(collection_file), 'w') as f:
    f.write(json.dumps(collection, indent=4))
