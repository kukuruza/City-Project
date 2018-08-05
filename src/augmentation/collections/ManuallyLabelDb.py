#!/usr/bin/env python
import os, os.path as op
import simplejson as json
import argparse
import logging
import numpy as np
import cv2
import sqlite3
from pprint import pprint, pformat

from collection_utilities import safeCopy, atcity


def maybeCreateTableClas(cursor):
  cursor.execute('''
      CREATE TABLE IF NOT EXISTS clas(
      class TEXT,
      model_id TEXT,
      collection_id TEXT,
      label TEXT,
      comment TEXT,
      PRIMARY KEY (class, model_id, collection_id)
  );''')
  cursor.execute('CREATE INDEX IF NOT EXISTS clas_class ON clas(class);')
  cursor.execute('CREATE INDEX IF NOT EXISTS clas_modelid ON clas(model_id);')
  cursor.execute('CREATE INDEX IF NOT EXISTS clas_modelid_collection ON clas(model_id, collection_id);')


def classify (cursor, class_name, key_dict, db_constraint='1'):
  ''' Assign a name to each car (currently most names reflect car type) '''

  cursor.execute('SELECT collection_id,model_id,error FROM cad WHERE %s' % db_constraint)
  cad_entries = cursor.fetchall()
  logging.info('Found %d cad models' % len(cad_entries))

  def getExamplePath(collection_id, model_id):
    example_path = atcity(op.join('data/augmentation/CAD/%s/examples/%s.png' %
        (collection_id, model_id)))
    assert op.exists(op.dirname(example_path)), 'Dir of %s must exist' % example_path
    return example_path

  # Number of working examples.
  num_good = np.sum([1 if op.exists(getExamplePath(collection_id, model_id)) else 0 
                     for collection_id, model_id, _ in cad_entries])
  logging.info('Found %d good examples.' % num_good)
  if num_good == 0:
    return

  button = 0
  i = 0
  while True:

    # Going in a loop.
    if i == -1:
      logging.info('Looping to the last model.')
    if i == len(cad_entries):
      logging.info('Looping to the first model.')
    i = i % len(cad_entries)

    collection_id, model_id, error = cad_entries[i]
    logging.info('i: %d model_id: %s, collection_id %s' % (i, model_id, collection_id))
    if error is not None:
      logging.info('error: %s' % error)

    # Load the model's current label.
    cursor.execute('SELECT label FROM clas WHERE model_id=? AND collection_id=? AND class=?',
         (model_id, collection_id, class_name))
    labels = cursor.fetchall()
    if len(labels) == 0:
      label = None
    elif len(labels) == 1:
      label = labels[0][0]
    else:
      raise Exception('Too many labels for %s' % (model_id, collection_id, class_name))
    logging.debug('Current label is %s' % label)

    # Load the example image.
    example_path = getExamplePath(collection_id, model_id)
    if not op.exists(example_path):
      logging.info('Example image does not exist: %s' % example_path)
      i += 1
      continue
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
    for key in key_dict:
      if button == ord(key):
        i += 1
        logging.debug('Button %s' % key)
        label = key_dict[key]

        # Update or insert.
        if len(labels) == 0:
          s = 'INSERT INTO clas(class,collection_id,model_id,label) VALUES (?,?,?,?)'
          logging.debug('Will execute: %s' % s)
          cursor.execute(s, (class_name, collection_id, model_id, label))
        elif len(labels) == 1:
          s = 'UPDATE clas SET class=?, collection_id=?, model_id=?, label=? ' \
              'WHERE class=? AND collection_id=? AND model_id=?;'
          logging.debug('Will execute: %s' % s)
          cursor.execute(s, (class_name, collection_id, model_id, label, 
                             class_name, collection_id, model_id))
        else:
          assert False


if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('--in_db_file', required=True)
  parser.add_argument('--out_db_file', default=':memory:')
  parser.add_argument('--class_name', required=True)
  parser.add_argument('--key_dict_json', required=True,
      help='Which label in db each key will correspond. '
      'For class_name="problem" '
      '{"g": "matte glass", "t": "triangles", "c": "no color", "o": "other"}. '
      'For class_name="color" '
      '{"w": "white", "k": "black", "e": "gray", "r": "red", "y": "yellow", '
      '"g": "green", "b": "blue", "o": "orange"}. '
      'For class_name="type" '
      '{"s": "sedan", "c": "taxi", "t": "truck", "v": "van", "b": "bus"}.')
  parser.add_argument('--logging', type=int, default=20)
  args = parser.parse_args()

  logging.basicConfig(level=args.logging, format='%(levelname)s: %(message)s')

  # Backup the db, and maybe create the table.
  safeCopy(args.in_db_file, args.out_db_file)
  conn = sqlite3.connect(args.out_db_file)
  cursor = conn.cursor()
  maybeCreateTableClas(cursor)

  # Parse key_dict_json.
  key_dict = json.loads(args.key_dict_json)
  logging.info('Key_dict:\n%s' % pformat(key_dict))

  classify(cursor, args.class_name, key_dict)

  conn.commit()
  conn.close()
