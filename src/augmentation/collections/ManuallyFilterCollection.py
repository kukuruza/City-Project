#!/usr/bin/env python
import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import simplejson as json
import argparse
import logging
import subprocess
import shutil
import numpy as np
import cv2
import traceback
from learning.helperSetup import setupLogging, atcity, _setupCopyDb_
from learning.helperSetup import setParamUnlessThere, assertParamIsThere
from learning.helperKeys import KeyReaderUser, getCalibration
from pprint import pprint



def classify (collection):
  ''' Assign a name to each car (currently most names reflect car type) '''

  keys = getCalibration()
  keys[ord('h')] = 'vehicle'    # but can't see the type, or not in the list
  keys[ord(' ')] = 'sedan'      # generic small car
  keys[ord('d')] = 'double'     # several cars stacked into one bbox
  keys[ord('c')] = 'taxi'       # (cab)
  keys[ord('t')] = 'truck'
  keys[ord('v')] = 'van'        # (== a small truck)
  keys[ord('m')] = 'minivan'
  keys[ord('b')] = 'bus'
  keys[ord('p')] = 'pickup'
  keys[ord('l')] = 'limo'
  keys[ord('s')] = 'suv'
  keys[ord('o')] = 'object'     # not a car, pedestrian, or bike
  keys[ord('k')] = 'bike'       # (bike or motobike)

  collection_id = collection['collection_id']
  models = collection['vehicles']
  collection_dir = 'augmentation/CAD/%s' % collection_id

  car_statuses = [''] * len(models)
  button = 0
  index = 0
  while button != 27 and index >= 0 and index < len(models):
    model = models[index]
    if logging.getLogger().getEffectiveLevel() == logging.DEBUG: pprint (model)
    if model['valid'] == False:
      index += 1
      continue

    example_file = op.join(collection_dir, 'examples/%s.png' % model['model_id'])
    example = cv2.imread(atcity(example_file))
    assert example is not None, example_file
    label = car_statuses[index] if car_statuses[index] != '' else model['vehicle_type']
    logging.info ('label: %s' % label)

    font = cv2.FONT_HERSHEY_SIMPLEX
    color = (0,255,255)
    thickness = 2
    cv2.putText (example, label, (50,50), font, 2, color, thickness)
    cv2.imshow('show', example)
    button = cv2.waitKey(-1)

    if button == keys['left']:
      logging.debug ('prev car')
      index -= 1
    elif button == keys['right']:
      logging.debug ('next car')
      index += 1
    elif button == keys['del']:
      logging.info ('delete')
      car_statuses[index] = 'badcar'
      index += 1
    elif button in keys.keys():  # any of the names added to keys in this function
      logging.info (keys[button])
      car_statuses[index] = keys[button]
      index += 1

  # actually delete or update
  for index in range(len(models)):
    model = models[index]
    model['description'] = None  # FIXME: remove
    status = car_statuses[index]
    if status == 'badcar':
      logging.info('model %s is deleted')
      model['valid'] = False
      model['ready'] = False
      model['error'] = 'user decided'
    elif status == '':
      logging.info ('model %s is not changed' % model['model_id'])
      pass
    else:
      logging.info('model %s assigned type %s' % (model['model_id'], status))
      model['vehicle_type'] = status




parser = argparse.ArgumentParser()
parser.add_argument('--collection_id')
parser.add_argument('--logging_level', type=int, default=20)
args = parser.parse_args()

setupLogging('log/augmentation/ManuallyFilterCollection.log', args.logging_level, 'w')

collection_file = 'augmentation/CAD/%s/readme-blended.json' % args.collection_id
backup_file     = 'augmentation/CAD/%s/unfiltered.json' % args.collection_id
# copy collection_file to backup_file
_setupCopyDb_ (atcity(collection_file), atcity(backup_file))

collection = json.load(open(atcity(collection_file)))
logging.info ('found %d models in the collection' % len(collection['vehicles']))

classify(collection)
pprint (collection)

with open(atcity(collection_file), 'w') as f:
  f.write(json.dumps(collection, indent=4))

# cad = Cad()
#
# update models
# collection_path = op.join(collection_dir, 'readme-blended.json')
# collection = json.load(open(collection_path))
# for model in collection['vehicles']:
#     cad.update_model (model, args.collection_id)
# with open(collection_path, 'w') as f:
#     f.write(json.dumps(collection, indent=4))
