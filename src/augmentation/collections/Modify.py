#!/usr/bin/env python
import os, os.path as op
import simplejson as json
import argparse
import logging
import numpy as np
import cv2
import sqlite3
from pprint import pprint, pformat
import matplotlib.pyplot as plt
import subprocess
import traceback

from collectionUtilities import safeConnect, atcity, getExamplePath, getBlendPath, WORK_DIR
from collectionDb import maybeCreateTableCad, maybeCreateTableClas, getAllCadColumns


def _queryCollectionsAndModels(cursor, clause):
  s = 'SELECT collection_id, model_id FROM cad %s;' % clause
  logging.debug('Will execute: %s' % s)
  cursor.execute(s)
  entries = cursor.fetchall()
  logging.info('Found %d entries' % len(entries))
  return entries


def _renderExample (collection_id, model_id, overwrite):

  example_path = getExamplePath(collection_id, model_id)
  if not overwrite and op.exists(example_path):
    logging.info ('skipping existing example %s' % example_path)
    return

  blend_path = getBlendPath(collection_id, model_id)
  if not op.exists(blend_path):
    logging.info ('skipping non-existing %s' % blend_path)
    return

  model = {
      'model_id': model_id,
      'collection_id': collection_id,
      'blend_file': blend_path,
      'example_file': example_path
  }
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


def _importCollection(cursor, collection, overwrite):
  cols = getAllCadColumns()

  for model in collection['vehicles']:
    try:
      model['collection_id'] = collection['collection_id']
      model['dims_L'] = None
      model['dims_W'] = None
      model['dims_H'] = None
      try:
        model['dims_L'] = model['dims_true']['x']
      except:
        pass
      try:
        model['dims_W'] = model['dims_true']['y']
      except:
        pass
      try:
        model['dims_H'] = model['dims_true']['z']
      except:
        pass

      # Convenience variable.
      modelcol = model['model_id'], model['collection_id']

      # Check if the model is already in this collection.
      cursor.execute('SELECT COUNT(1) FROM cad WHERE model_id=? AND collection_id=?', modelcol)
      num_present = cursor.fetchone()[0]
      assert num_present <= 1, 'Primary key restriction: %s' % model['model_id']

      # Check if there is already such a model in a different collection.
      cursor.execute('SELECT collection_id FROM cad WHERE model_id=? AND collection_id!=?', modelcol)
      valid_collection_ids = cursor.fetchall()
      if len(valid_collection_ids) >= 1:
        model['error'] = 'already in collection(s) %s' % str(valid_collection_ids)
        logging.warning('Model %s is %s' % (model['model_id'], model['error']))

      if num_present == 1 and not overwrite:
        logging.warning('Skipping model %s in collection %s, because it is already there.' % modelcol)
        continue

      elif num_present == 0:
        logging.info('Inserting model %s from collection %s' % modelcol)
        s = 'INSERT INTO cad(%s) VALUES (%s)' % (','.join(cols), ','.join(['?'] * len(cols)))

      elif num_present == 1 and overwrite:
        logging.info('Updating model %s from collection %s' % modelcol)
        s = 'UPDATE cad SET %s WHERE model_id=? AND collection_id=?' % ','.join(['%s=?' % c for c in cols[2:]])
        cols = cols[2:] + cols[:2]  # model_id and collection_id are looped to the back of str.

      logging.debug('Will execute: %s' % s)
      # Form an entry of values, valid for both INSERT and UPDATE.
      entry = tuple([model[name] if name in model else None for name in cols])
      logging.debug(str(entry))
      cursor.execute(s, entry)
      
    # To debug a problem in json, we need to print all info before exiting
    except Exception:
      print('Error occured in model: \n%s' % pformat(model))
      traceback.print_exc()
      sys.exit()


def importCollectionsParser(subparsers):
  parser = subparsers.add_parser('importCollections',
    description='Import json file with the collection.')
  parser.add_argument('--collection_ids', nargs='+', required=True)
  parser.add_argument('--overwrite', action='store_true')
  parser.set_defaults(func=importCollections)

def importCollections(cursor, args):

  for collection_id in args.collection_ids:
    json_path = atcity('data/augmentation/CAD/%s/collection.json' % collection_id)
    collection = json.load(open(json_path))
    logging.info('Found %d models in the collection' % len(collection['vehicles']))

    _importCollection(cursor, collection, args.overwrite)


def renderExamplesParser(subparsers):
  parser = subparsers.add_parser('renderExamples',
    description='Render an example for each model.')
  parser.add_argument('--overwrite', action='store_true')
  parser.set_defaults(func=renderExamples)

def renderExamples(cursor, args):
  for entry in _queryCollectionsAndModels(cursor, args.clause):
    _renderExample(entry, args.overwrite)


def classifyParser(subparsers):
  parser = subparsers.add_parser('classify',
    description='Manually assign/change a property for each model.')
  parser.add_argument('--class_name', required=True)
  parser.add_argument('--key_dict_json', required=True,
      help='Which label in db each key will correspond. '
      'For class_name="issue" '
      '{"g": "matte glass", "t": "triangles", "c": "no color", "o": "other"}. '
      'For class_name="color" '
      '{"w": "white", "k": "black", "e": "gray", "r": "red", "y": "yellow", '
      '"g": "green", "b": "blue", "o": "orange"}. '
      'For class_name="domain" '
      '{"f": "fiction", "m": "military", "e": "emergency"}.'
      'For class_name="type1" '
      '{" ": "passenger", "t": "truck", "v": "van", "b": "bus", "c": "bike"}.')
  parser.set_defaults(func=classify)

def classify(cursor, args):

  # Parse a string into a dict.
  key_dict = json.loads(args.key_dict_json)
  logging.info('Key_dict:\n%s' % pformat(key_dict))

  # Remove those that cant be rendered.
  removeAllWithoutRender(cursor, args=argparse.Namespace(clause=''))

  entries = _queryCollectionsAndModels(cursor, args.clause)
  logging.info('Found %d model with .blend files.' % len(entries))
  if len(entries) == 0:
    return

  button = 0
  i = 0
  while True:

    # Going in a loop.
    if i == -1:
      logging.info('Looping to the last model.')
    if i == len(entries):
      logging.info('Looping to the first model.')
    i = i % len(entries)

    collection_id, model_id = entries[i]
    logging.info('i: %d model_id: %s, collection_id %s' % (i, model_id, collection_id))

    # Load the model's current label.
    cursor.execute('SELECT label FROM clas WHERE model_id=? AND collection_id=? AND class=?',
         (model_id, collection_id, args.class_name))
    labels = cursor.fetchall()
    if len(labels) == 0:
      label = None
    elif len(labels) == 1:
      label = labels[0][0]
    else:
      raise Exception('Too many labels for %s' % (model_id, collection_id, args.class_name))
    logging.debug('Current label is %s' % label)

    # Load the example image.
    example_path = getExamplePath(collection_id, model_id)
    assert op.exists(example_path), example_path
    image = cv2.imread(example_path)
    assert image is not None, example_path

    # Display
    font = cv2.FONT_HERSHEY_SIMPLEX
    color = (0,255,255)
    thickness = 2
    cv2.putText (image, label, (50,50), font, 2, color, thickness)
    cv2.imshow('show', image)
    button = cv2.waitKey(-1)
    logging.debug('User pressed button: %d' % button)

    if button == 27:
      break
    elif button == ord('-'):
      logging.debug('Previous car.')
      i -= 1
    elif button == ord('='):
      logging.debug('Next car.')
      i += 1
    elif button == 127:  # Delete.
      logging.debug('Button "delete"')
      i += 1
      s = 'DELETE FROM clas WHERE class=? AND collection_id=? AND model_id=?'
      logging.debug('Will execute: %s' % s)
      cursor.execute(s, (args.class_name, collection_id, model_id))
    else:
      for key in key_dict:
        if button == ord(key):
          i += 1
          logging.debug('Button %s' % key)
          label = key_dict[key]

          # Update or insert.
          if len(labels) == 0:
            s = 'INSERT INTO clas(label,class,collection_id,model_id) VALUES (?,?,?,?)'
          elif len(labels) == 1:
            s = 'UPDATE clas SET label=? WHERE class=? AND collection_id=? AND model_id=?;'
          else:
            assert False
          logging.debug('Will execute: %s' % s)
          cursor.execute(s, (label, args.class_name, collection_id, model_id))
          break  # Key iteration.



def fillInDimsParser(subparsers):
  parser = subparsers.add_parser('fillInDims',
    description='Fill in the dimensions fields with actual dimensions.')
  parser.set_defaults(func=fillInDims)

def fillInDims(cursor, args):

  # Remove those that cant be rendered.
  removeAllWithoutRender(cursor, args=argparse.Namespace(clause=''))

  for idx, (collection_id, model_id) in enumerate(_queryCollectionsAndModels(cursor, args.clause)):
    logging.info('Model idx: %d' % idx)

    model = {'blend_file': getBlendPath(collection_id, model_id)}
    model_path = op.join(WORK_DIR, 'model.json')
    with open(model_path, 'w') as f:
      f.write(json.dumps(model, indent=4))

    try:
      command = ['%s/blender' % os.getenv('BLENDER_ROOT'), '--background', '--python',
                 atcity('src/augmentation/collections/getDims.py')]
      returncode = subprocess.call (command, shell=False)
      logging.debug('Blender returned code %s' % str(returncode))

      dims = json.load(open(model_path))['dims']
      dims_L, dims_W, dims_H = dims['x'], dims['y'], dims['z']
      logging.info('collection_id: %s, model_id: %s, L: %.2f, W: %.2f, H: %.2f' % 
          (collection_id, model_id, dims_L, dims_W, dims_H))
      s = 'UPDATE cad SET dims_L=?, dims_W=?, dims_H=? WHERE collection_id=? AND model_id=?;'
      logging.debug('Will execute: %s' % s)
      cursor.execute(s, (dims_L, dims_W, dims_H, collection_id, model_id))

    except:
      logging.error('Failed: %s' % traceback.format_exc())
      continue


def removeAllWithoutRenderParser(subparsers):
  parser = subparsers.add_parser('removeAllWithoutRender',
    description='Remove all models without rendered example as having an issue.')
  parser.set_defaults(func=removeAllWithoutRender)

def removeAllWithoutRender (cursor, args):

  for collection_id, model_id in _queryCollectionsAndModels(cursor, args.clause):

    example_path = getExamplePath(collection_id, model_id)
    if not op.exists(example_path):
      logging.debug('Example image does not exist: %s' % example_path)

      s = 'DELETE FROM clas WHERE collection_id=? AND model_id=?'
      logging.debug('Will execute: %s' % s)
      cursor.execute(s, (collection_id, model_id))

      s = 'DELETE FROM cad WHERE collection_id=? AND model_id=?'
      logging.debug('Will execute: %s' % s)
      cursor.execute(s, (collection_id, model_id))

  cursor.execute('SELECT cad.collection_id, cad.model_id FROM cad %s;' % args.clause)
  entries = cursor.fetchall()
  logging.info('There are %d cad models with render.' % len(entries))


def removeDuplicatesParser(subparsers):
  parser = subparsers.add_parser('removeDuplicates',
    description='Remove all models with duplicate model_id from other collections.')
  parser.set_defaults(func=removeDuplicates)

def removeDuplicates(cursor, args):

  s = 'SELECT COUNT(cad.model_id) - COUNT(DISTINCT(cad.model_id)) FROM cad %s;' % args.clause
  logging.debug('Will execute: %s' % s)
  cursor.execute(s)
  num_duplicates = cursor.fetchone()[0]
  logging.info('Found %d duplicates.' % num_duplicates)

  s = 'SELECT DISTINCT(cad.model_id) FROM cad %s;' % args.clause
  logging.debug('Will execute: %s' % s)
  cursor.execute(s)
  model_ids = cursor.fetchall()
  logging.info('Found %d distinct model ids' % len(model_ids))

  for model_id, in model_ids:

    s = 'SELECT collection_id FROM cad WHERE model_id=?;'
    cursor.execute(s, (model_id,))
    collection_ids = cursor.fetchall()

    # Not a duplicate, skip.
    if len(collection_ids) == 1:
      continue

    # Keep the first model.
    del collection_ids[0]

    # Remove the rest.
    for collection_id, in collection_ids:

      s = 'DELETE FROM clas WHERE collection_id=? AND model_id=?'
      logging.debug('Will execute: %s' % s)
      cursor.execute(s, (collection_id, model_id))

      s = 'DELETE FROM cad WHERE collection_id=? AND model_id=?'
      logging.debug('Will execute: %s' % s)
      cursor.execute(s, (collection_id, model_id))


def makeGridParser(subparsers):
  parser = subparsers.add_parser('makeGrid',
    description='Combine renders of models that satisfy a "where" into a grid.')
  parser.add_argument('--swidth', type=int, help='Width to crop. If not specified, use model-dependent crop.')
  parser.add_argument('--display', action='store_true')
  parser.add_argument('--cols', type=int, default=4, help='number of columns.')
  parser.add_argument('--dwidth', type=int, default=512, help='output width of a cell')
  parser.add_argument('--dheight', type=int, default=384, help='output height of a cell')
  parser.add_argument('--out_path')
  parser.set_defaults(func=makeGrid)

def makeGrid (cursor, args):

  # Load empty image.
  if not args.swidth:
    empty_path = atcity('data/augmentation/scenes/empty-import.png')
    if not op.exists(empty_path):
      raise Exception('Empty image does not exist.')
    empty = cv2.imread(empty_path)
    if empty is None:
      raise Exception('Failed to load empty image.')

  # Remove all models without render and duplicates.
  removeAllWithoutRender(cursor, args)
  removeDuplicates(cursor, args)

  entries = _queryCollectionsAndModels(cursor, args.clause)

  if len(entries) == 0:
    logging.info('Nothing is found.')
    return

  rows = len(entries) // args.cols + (0 if len(entries) % args.cols == 0 else 1)
  logging.info('Grid is of element shape %d x %d' % (rows, args.cols))
  grid = np.ones(shape=(rows * args.dheight, args.cols * args.dwidth, 3), dtype=np.uint8) * 64
  logging.info('Grid is of pixel shape %d x %d' % (rows * args.dheight, args.cols * args.dwidth))

  def getExamplePath(collection_id, model_id):
    example_path = atcity(op.join('data/augmentation/CAD/%s/examples/%s.png' %
        (collection_id, model_id)))
    assert op.exists(op.dirname(example_path)), 'Dir of %s must exist' % example_path
    return example_path

  for idx, (collection_id, model_id) in enumerate(entries):

    example_path = getExamplePath(collection_id, model_id)
    if not op.exists(example_path):
      logging.debug('Example image does not exist: %s' % example_path)

    render = cv2.imread(example_path)
    if render is None:
      logging.error('Image %s failed to be read' % example_path)
      continue

    h_to_w = args.dheight / args.dwidth

    if args.swidth:  # Manually given crop.
      sheight = int(args.swidth * h_to_w)
      y1 = render.shape[0] // 2 - sheight // 2
      y2 = y1 + sheight
      x1 = render.shape[1] // 2 - args.swidth // 2
      x2 = x1 + args.swidth
      crop = render[y1:y2, x1:x2]

    else:  # Model-dependent crop.
      # Find tight crop.
      mask = (render - empty) != 0
      nonzeros = mask.nonzero()
      y1 = nonzeros[0].min()
      x1 = nonzeros[1].min()
      y2 = nonzeros[0].max()
      x2 = nonzeros[1].max()
      swidth = x2 - x1
      sheight = y2 - y1
      # Adjust to keep the ratio fixed.
      if sheight < h_to_w * swidth:
        sheight = int(swidth * h_to_w)
        y1 = int((y2 + y1) / 2 - sheight / 2)
        y2 = y1 + sheight
      else:
        swidth = int(sheight / h_to_w)
        x1 = int((x2 + x1) / 2 - swidth / 2)
        x2 = x1 + swidth
      logging.debug('Crop at: y1=%d, x1=%d, y2=%d, x2=%d.' % (y1, x1, y2, x2))
      if logging.getLogger().getEffectiveLevel() <= 10:
        diff = render - empty
        diff = cv2.rectangle(diff, (x1,y1), (x2,y2), (0,255,0), 1)
        cv2.imshow('diff', diff)
        cv2.waitKey(-1)
      # Add the padding in case the box went  and crop.
      H, W = render.shape[:2]
      render = np.pad(render, pad_width=((H,H),(W,W),(0,0)), mode='constant', constant_values=64)
      crop = render[y1+H : y2+H, x1+W : x2+W]

    crop = cv2.resize(crop, dsize=(args.dwidth, args.dheight))

    x1 = idx % args.cols * args.dwidth
    y1 = idx // args.cols * args.dheight
    logging.debug('Idx: %03d, x1: %05d, y1: %05d, collection_id: %s, model_id: %s' % 
        (idx, x1, y1, collection_id, model_id))
    grid[y1 : y1 + args.dheight, x1 : x1 + args.dwidth] = crop

  if args.display:
    cv2.imshow('grid', grid)
    cv2.waitKey(-1)

  if args.out_path:
    cv2.imwrite(args.out_path, grid)
    

def plotHistogramParser(subparsers):
  parser = subparsers.add_parser('plotHistogram',
    description='Get a 1d histogram plot of fields.')
  parser.set_defaults(func=plotHistogram)
  #parser.add_argument('-x', required=True)
  parser.add_argument('--query', required=True, help='e.g., SELECT car_make FROM cad.')
  parser.add_argument('--ylog', action='store_true')
  parser.add_argument('--bins', type=int)
  parser.add_argument('--xlabel', default='')
  parser.add_argument('--rotate_xticklabels', action='store_true')
  parser.add_argument('--categorical', action='store_true')
  parser.add_argument('--display', action='store_true', help='show on screen.')
  parser.add_argument('--out_path', help='if specified, will save the plot to this file.')

def plotHistogram(cursor, args):

  # Remove all models without render and duplicates.
  removeAllWithoutRender(cursor, args=argparse.Namespace(clause=''))
  removeDuplicates(cursor, args=argparse.Namespace(clause=''))

  cursor.execute(args.query)
  entries = cursor.fetchall()

  xlist = [x if x is not None else 'unlabelled' for x, in entries]
  if not xlist:
    logging.info('No cars, nothing to draw.')
    return
  logging.debug(str(xlist))

  fig, ax = plt.subplots()
  if args.categorical:
    import pandas as pd
    import seaborn as sns
    if args.rotate_xticklabels:
      plt.xticks(rotation=90)
    data = pd.DataFrame({args.xlabel: xlist})
    ax = sns.countplot(x=args.xlabel, data=data, order=data[args.xlabel].value_counts().index)
    plt.tight_layout()
  else:
    if args.bins:
      ax.hist(xlist, args.bins)
    else:
      ax.hist(xlist)

  if args.ylog:
    ax.set_yscale('log', nonposy='clip')
  #plt.xlabel(args.x if args.xlabel else '')
  plt.ylabel('')
  if args.out_path:
    logging.info('Saving to %s' % args.out_path)
    plt.savefig(args.out_path)
  if args.display:
    plt.show()


def manuallyEditInBlenderParser(subparsers):
  parser = subparsers.add_parser('manuallyEditInBlender',
    description='For each model there is an option to edit and save its blender file.')
  parser.set_defaults(func=manuallyEditInBlender)

def manuallyEditInBlender(cursor, args):

  # Remove all models without render.
  removeAllWithoutRender(cursor, args=argparse.Namespace(clause=''))

  entries = _queryCollectionsAndModels(cursor, args.clause)

  button = 0
  i = 0
  while True:

    # Going in a loop.
    if i == -1:
      logging.info('Looping to the last model.')
    if i == len(entries):
      logging.info('Looping to the first model.')
    i = i % len(entries)

    collection_id, model_id = entries[i]
    logging.info('i: %d model_id: %s, collection_id %s' % (i, model_id, collection_id))

    # Load the example image.
    example_path = getExamplePath(collection_id, model_id)
    assert op.exists(example_path), example_path
    image = cv2.imread(example_path)
    assert image is not None, example_path

    cv2.imshow('show', image)
    button = cv2.waitKey(-1)
    logging.debug('User pressed button: %d' % button)

    if button == 27:
      break
    elif button == ord('-'):
      logging.debug('Previous car.')
      i -= 1
    elif button == ord('='):
      logging.debug('Next car.')
      i += 1
    elif button == 32:  # Space
      logging.debug('Button "space", will edit.')
      # i += 1
      try:
        command = ['%s/blender' % os.getenv('BLENDER_ROOT'),
                   getBlendPath(collection_id, model_id)]
        returncode = subprocess.call (command, shell=False)
        logging.debug('Blender returned code %s' % str(returncode))
        # Re-render.
        _renderExample (collection_id, model_id, overwrite=True)
      except:
        logging.error('Failed: %s' % traceback.format_exc())
        continue


if __name__ == "__main__":

  parser = argparse.ArgumentParser('Do one of the automatic operations on a db.')
  parser.add_argument('--in_db_file', required=True)
  parser.add_argument('--out_db_file', default=':memory:')
  parser.add_argument('--clause', default='', help='SQL WHERE clause.')
  parser.add_argument('--logging', type=int, default=20)
  parser.add_argument('--dry_run', action='store_true',
      help='Do not commit (for debugging).')

  subparsers = parser.add_subparsers()
  importCollectionsParser(subparsers)
  removeAllWithoutRenderParser(subparsers)
  makeGridParser(subparsers)
  removeDuplicatesParser(subparsers)
  plotHistogramParser(subparsers)
  fillInDimsParser(subparsers)
  manuallyEditInBlenderParser(subparsers)
  renderExamplesParser(subparsers)
  classifyParser(subparsers)

  args = parser.parse_args()

  logging.basicConfig(level=args.logging, format='%(levelname)s: %(message)s')

  # Backup the db.
  conn = safeConnect(args.in_db_file, args.out_db_file)
  cursor = conn.cursor()
  maybeCreateTableCad(cursor)
  maybeCreateTableClas(cursor)

  args.func(cursor, args)

  if not args.dry_run:
    logging.info('Committing changes.')
    conn.commit()
  conn.close()
