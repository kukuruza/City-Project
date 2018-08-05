#!/usr/bin/env python
import sys, os, os.path as op
import json
import argparse
import logging
import subprocess
import shutil
import traceback
import progressbar
from collection_utilities import atcity


WORK_DIR = atcity('data/augmentation/blender/current-collection')


def render_example (model, overwrite):

  collection_id = model['collection_id']
  model_id      = model['model_id']

  collection_dir = 'data/augmentation/CAD/%s' % collection_id
  blend_file   = op.join(collection_dir, 'blend/%s.blend' % model_id)
  example_file = op.join(collection_dir, 'examples/%s.png' % model_id)
  model['blend_file']   = blend_file
  model['example_file'] = example_file

  if not overwrite and op.exists(example_file):
    logging.info ('skipping existing example %s' % example_file)
    return

  if not op.exists(atcity(blend_file)):
    logging.info ('skipping non-existing %s' % blend_file)
    return

  model_path = op.join(WORK_DIR, 'model.json')
  with open(model_path, 'w') as f:
    f.write(json.dumps(model, indent=2))

  try:
    command = ['%s/blender' % os.getenv('BLENDER_ROOT'), '--background', '--python',
               atcity('src/augmentation/collections/renderExample.py')]
    returncode = subprocess.call (command, shell=False)
    logging.info ('blender returned code %s' % str(returncode))
  except:
    logging.error('failed: %s' % traceback.format_exc())
    return


if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('--collection_id')
  parser.add_argument('--model_ids', nargs='+')
  parser.add_argument('--overwrite', action='store_true')
  parser.add_argument('--logging', type=int, default=20)
  args = parser.parse_args()

  #progressbar.streams.wrap_stderr()
  logging.basicConfig(level=args.logging, format='%(levelname)s: %(message)s')

  collection_file = 'data/augmentation/CAD/%s/collection.json' % args.collection_id
  collection = json.load(open(atcity(collection_file)))

  logging.info ('found %d models in the collection' % len(collection['vehicles']))

  for model in collection['vehicles']:
    if args.model_ids is None or model['model_id'] in args.model_ids:
      logging.info('model_id %s' % model['model_id'])
      model['collection_id'] = args.collection_id
      render_example(model, overwrite=args.overwrite)
