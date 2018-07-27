import sys, os, os.path as op
import simplejson as json
import numpy as np
from argparse import ArgumentParser
import progressbar
import logging
import sqlite3

from collection_utilities import backupFile, atcity


def doesTableExist(cursor, table):
  cursor.execute('''SELECT count(*) FROM sqlite_master 
                    WHERE name=? AND type='table';''', (table,))
  return cursor.fetchone()[0] != 0


def createTableCad(cursor):
  cursor.execute('''
      CREATE TABLE IF NOT EXISTS cad(
      model_id TEXT,
      collection_id TEXT,
      model_name TEXT,
      description TEXT, 
      valid INTEGER, 
      ready INTEGER, 
      error TEXT,
      car_make TEXT,
      car_year TEXT,
      car_model TEXT,
      color TEXT,
      L_model REAL,
      W_model REAL,
      H_model REAL,
      L_real REAL,
      W_real REAL,
      H_real REAL,
      PRIMARY KEY (model_id, collection_id)
  );''')
  cursor.execute('CREATE INDEX cad_modelid ON cad(model_id);')
  cursor.execute('CREATE INDEX cad_modelid_collection ON cad(model_id, collection_id);')

def getAllCadColumns():
  return [
      'model_id',
      'collection_id',
      'model_name',
      'description', 
      'valid', 
      'ready', 
      'error',
      'car_make',
      'car_year',
      'car_model',
      'color',
      'L_model',
      'W_model',
      'H_model',
      'L_real',
      'W_real',
      'H_real'
  ]

def exportCollection(cursor, collection):
  ''' Export a dict with collection to sqlite3 db. '''

  # Get a list of column names.
  cols = getAllCadColumns()

  for model in progressbar.ProgressBar()(collection['vehicles']):
    model['collection_id'] = collection['collection_id']
    model['L_model'] = model['dims']['x'] if 'dims' in model else None
    model['W_model'] = model['dims']['y'] if 'dims' in model else None
    model['H_model'] = model['dims']['z'] if 'dims' in model else None
    model['L_real'] = model['dims_true']['x'] if 'dims_true' in model else None
    model['W_real'] = model['dims_true']['y'] if 'dims_true' in model else None
    model['H_real'] = model['dims_true']['z'] if 'dims_true' in model else None

    # Check if alreday has this same model.
    cursor.execute('SELECT COUNT(*) FROM cad WHERE model_id=? AND collection_id=?',
        (model['model_id'], model['collection_id']))
    if cursor.fetchone()[0] > 0:
      logging.error('Model-collection %s - %s is already in the db' %
          (model['model_id'], model['collection_id']))
      continue

    # See if there is already such a model in other collection.
    cursor.execute('SELECT collection_id FROM cad WHERE model_id=? AND valid=1',
        (model['model_id'],))
    valid_collection_ids = cursor.fetchall()
    if len(valid_collection_ids) >= 1:
      logging.error('Found collections %s with the valid model %s' %
          (str(valid_collection_ids), model['model_id']))
      model['error'] = 'Already in collection(s) %s' % str(valid_collection_ids)
      model['valid'] = False
      model['ready'] = False
      if len(valid_collection_ids) > 1:
        logging.error('A problem in db: %d > 1 collections (%s) have valid model_id %s.' %
            len(valid_collection_ids), valid_collection_ids, model['model_id'])

    # Form a request string.
    s = 'INSERT INTO cad(%s) VALUES (%s)' % (','.join(cols), ','.join(['?'] * len(cols)))
    logging.debug('Will execute: %s' % s)
    # Form an entry of values.
    entry = tuple([model[name] if name in model else None for name in cols])
    logging.debug(str(entry))
    # Insert.
    cursor.execute(s, entry)


if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument('--logging', default=20, type=int, choices={10, 20, 30, 40},
      help='Log debug (10), info (20), warning (30), error (40).')
  parser.add_argument('--db_file', default=':memory:',
      help='Filepath of the output db, default is doing everything in memory.')
  parser.add_argument('--collection_id', required=True)
  args = parser.parse_args()

  progressbar.streams.wrap_stderr()
  logging.basicConfig(level=args.logging, format='%(levelname)s: %(message)s')

  # Open the collection and vehicle information.
  collection_file = 'data/augmentation/CAD/%s/collection.json' % args.collection_id
  collection = json.load(open(atcity(collection_file)))
  logging.info('found %d models in the collection' % len(collection['vehicles']))

  conn = sqlite3.connect(args.db_file)
  cursor = conn.cursor()
  if not doesTableExist(cursor, 'cad'):
    createTableCad(cursor)
  exportCollection(cursor, collection)

  conn.commit()
  