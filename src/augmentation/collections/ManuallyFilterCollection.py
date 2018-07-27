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
from pprint import pprint, pformat
from db.lib.helperSetup import setupLogging, atcity
from db.lib.helperKeys import KeyReaderUser, getCalibration



def classify (collection):
  ''' Assign a name to each car (currently most names reflect car type) '''

  keys = getCalibration()
  keys[ord(' ')] = 'sedan'
  keys[ord('c')] = 'taxi'
  keys[ord('t')] = 'truck'
  keys[ord('v')] = 'van'
  keys[ord('b')] = 'bus'
  keys[ord('o')] = 'object'

  collection_id = collection['collection_id']
  models = collection['vehicles']
  collection_dir = 'data/augmentation/CAD/%s' % collection_id
  indices = [i for i in range(len(models)) if models[i]['valid']]

  button = 0
  i = 0
  while i < len(indices):
    logging.debug('i: %d' % i)
    if i < 0:
      logging.warning('i < 0, reset to the first model')
      i = 0

    model = models[indices[i]]
    logging.info('model_id: %s' % model['model_id'])
    logging.debug(pformat(model))

    example_file = op.join(collection_dir, 'examples/%s.png' % model['model_id'])
    example = cv2.imread(atcity(example_file))
    assert example is not None, example_file
    label = model['vehicle_type'] if model['valid'] == True else 'invalid'
    logging.info ('label: %s' % label)

    font = cv2.FONT_HERSHEY_SIMPLEX
    color = (0,255,255)
    thickness = 2
    cv2.putText (example, label, (50,50), font, 2, color, thickness)
    cv2.imshow('show', example)
    button = cv2.waitKey(-1)
    logging.debug('user pressed button: %d' % button)

    if button == keys['esc']:
      break
    elif button == keys['left']:
      logging.debug ('prev car')
      i -= 1
    elif button == keys['right']:
      logging.debug ('next car')
      i += 1
    elif button == keys['del']:
      logging.info ('delete')
      model['valid'] = False
      model['error'] = 'user defined in ManuallyFilterCollection'
      logging.info('model %s made invalid' % model['model_id'])
      models[indices[i]] = model
      i += 1
    elif button in keys.keys():  # any of the names added to keys in this function
      logging.info (keys[button])
      model['vehicle_type'] = keys[button]
      logging.info('model %s assigned type %s' % (model['model_id'], model['vehicle_type']))
      models[indices[i]] = model
      i += 1

  for index in range(len(models)):
    model = models[index]
    if model['valid'] == False:
      model['ready'] = False
      example_file = op.join(collection_dir, 'examples/%s.png' % model['model_id'])
      if op.exists(atcity(example_file)):
        logging.info('removing example for non-valid model: %s' % model['model_id'])
        os.remove(atcity(example_file))
    models[index] = model


def problem (collection):
  ''' Assign problem of glass or triangulation or size. '''

  keys = getCalibration()
  keys[ord(' ')] = 'ok'
  keys[ord('g')] = 'glass'
  keys[ord('t')] = 'triangulation'
  keys[ord('s')] = 'size'
  keys[ord('o')] = 'other'
  keys[ord('c')] = 'no color'

  collection_id = collection['collection_id']
  models = collection['vehicles']
  collection_dir = 'data/augmentation/CAD/%s' % collection_id
  indices = [i for i in range(len(models)) if models[i]['valid']]

  button = 0
  i = 0
  while i < len(indices):
    logging.debug('i: %d' % i)
    if i < 0:
      logging.warning('i < 0, reset to the first model')
      i = 0

    model = models[indices[i]]
    logging.info('model_id: %s' % model['model_id'])
    logging.debug(pformat(model))

    example_file = op.join(collection_dir, 'examples/%s.png' % model['model_id'])
    example = cv2.imread(atcity(example_file))
    assert example is not None, example_file
    label = model['problem'] if 'problem' in model else ''
    logging.info ('label: %s' % label)

    font = cv2.FONT_HERSHEY_SIMPLEX
    color = (0,255,255)
    thickness = 2
    cv2.putText (example, label, (50,50), font, 2, color, thickness)
    cv2.imshow('show', example)
    button = cv2.waitKey(-1)
    logging.debug('user pressed button: %d' % button)

    if button == keys['esc']:
      break
    elif button == keys['left']:
      logging.debug ('prev car')
      i -= 1
    elif button == keys['right']:
      logging.debug ('next car')
      i += 1
    elif button in keys.keys():  # any of the names added to keys in this function
      logging.info (keys[button])
      model['problem'] = keys[button]
      logging.info('model %s assigned type %s' % (model['model_id'], model['problem']))
      models[indices[i]] = model
      i += 1


def color (collection):
  ''' Assign problem of glass or triangulation. '''

  keys = getCalibration()
  keys[ord(' ')] = ''
  keys[ord('w')] = 'white'
  keys[ord('k')] = 'black'
  keys[ord('e')] = 'gray'
  keys[ord('r')] = 'red'
  keys[ord('y')] = 'yellow'
  keys[ord('g')] = 'green'
  keys[ord('b')] = 'blue'
  keys[ord('o')] = 'orange'

  collection_id = collection['collection_id']
  models = collection['vehicles']
  collection_dir = 'data/augmentation/CAD/%s' % collection_id
  indices = [i for i in range(len(models)) if models[i]['valid']]

  button = 0
  i = 0
  while i < len(indices):
    logging.debug('i: %d' % i)
    if i < 0:
      logging.warning('i < 0, reset to the first model')
      i = 0

    model = models[indices[i]]
    logging.info('model_id: %s' % model['model_id'])
    logging.debug(pformat(model))

    example_file = op.join(collection_dir, 'examples/%s.png' % model['model_id'])
    example = cv2.imread(atcity(example_file))
    assert example is not None, example_file
    label = model['color'] if 'color' in model else ''
    logging.info ('label: %s' % label)

    font = cv2.FONT_HERSHEY_SIMPLEX
    color = (0,255,255)
    thickness = 2
    cv2.putText (example, label, (50,50), font, 2, color, thickness)
    cv2.imshow('show', example)
    button = cv2.waitKey(-1)
    logging.debug('user pressed button: %d' % button)

    if button == keys['esc']:
      break
    elif button == keys['left']:
      logging.debug ('prev car')
      i -= 1
    elif button == keys['right']:
      logging.debug ('next car')
      i += 1
    elif button in keys.keys():  # any of the names added to keys in this function
      logging.info (keys[button])
      if keys[button] != '':
        model['color'] = keys[button]
        logging.info('model %s assigned type %s' % (model['model_id'], model['color']))
      models[indices[i]] = model
      i += 1


if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('--task', choices=['type', 'color', 'problem'], required=True)
  parser.add_argument('--collection_id', required=True)
  parser.add_argument('--logging_level', type=int, default=20)
  args = parser.parse_args()

  setupLogging('log/augmentation/ManuallyFilterCollection.log', args.logging_level, 'w')

  collection_file = 'data/augmentation/CAD/%s/collection.json' % args.collection_id

  collection = json.load(open(atcity(collection_file)))
  logging.info ('found %d models in the collection' % len(collection['vehicles']))

  if args.task == 'problem':
    problem(collection)
  elif args.task == 'color':
    color(collection)
  elif args.task == 'type':
    classify(collection)
  else:
    raise Exception('Bad task.')
    
  pprint (collection)

  with open(atcity(collection_file), 'w') as f:
    f.write(json.dumps(collection, indent=4))
