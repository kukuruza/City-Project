import sys, os, os.path as op
import simplejson as json
import numpy as np
from argparse import ArgumentParser
import logging
import sqlite3
import traceback
from pprint import pformat

from collection_utilities import backupFile, atcity


def maybeCreateTableCad(cursor):
  cursor.execute('''
      CREATE TABLE IF NOT EXISTS cad(
      model_id TEXT,
      collection_id TEXT,
      model_name TEXT,
      description TEXT, 
      error TEXT,
      car_make TEXT,
      car_year TEXT,
      car_model TEXT,
      color TEXT,
      dims_L REAL,
      dims_W REAL,
      dims_H REAL,
      comment TEXT,
      PRIMARY KEY (model_id, collection_id)
  );''')
  cursor.execute('CREATE INDEX IF NOT EXISTS cad_modelid ON cad(model_id);')
  cursor.execute('CREATE INDEX IF NOT EXISTS cad_modelid_collection ON cad(model_id, collection_id);')

def getAllCadColumns():
  return [
      'model_id',
      'collection_id',
      'model_name',
      'description', 
      'error',
      'car_make',
      'car_year',
      'car_model',
      'color',
      'dims_L',
      'dims_W',
      'dims_H',
      'comment'
  ]

def exportCollection(cursor, collection):
  ''' Export a dict with collection to sqlite3 db. '''

  # Get a list of column names.
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

      # Check if alreday has this same model.
      cursor.execute('SELECT COUNT(*) FROM cad WHERE model_id=? AND collection_id=?',
          (model['model_id'], model['collection_id']))
      if cursor.fetchone()[0] > 0:
        logging.error('Model-collection %s - %s is already in the db' %
            (model['model_id'], model['collection_id']))
        continue

      # See if there is already such a model in other collection.
      cursor.execute('SELECT collection_id FROM cad WHERE model_id=? AND error IS NOT NULL',
          (model['model_id'],))
      valid_collection_ids = cursor.fetchall()
      if len(valid_collection_ids) >= 1:
        logging.error('Found collections %s with the valid model %s' %
            (str(valid_collection_ids), model['model_id']))
        model['error'] = 'Already in collection(s) %s' % str(valid_collection_ids)
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

    # To debug a problem in json, we need to print all info before exiting
    except Exception, err:
      print('Error occured in model: \n%s' % pformat(model))
      traceback.print_exc()
      sys.exit()



if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument('--logging', default=20, type=int, choices={10, 20, 30, 40},
      help='Log debug (10), info (20), warning (30), error (40).')
  parser.add_argument('--db_file', default=':memory:',
      help='Filepath of the output db, default is doing everything in memory.')
  parser.add_argument('--collection_ids', nargs='+', required=True)
  args = parser.parse_args()

  logging.basicConfig(level=args.logging, format='%(levelname)s: %(message)s')

  conn = sqlite3.connect(args.db_file)
  cursor = conn.cursor()
  maybeCreateTableCad(cursor)

  for collection_id in args.collection_ids:

    collection_file = 'data/augmentation/CAD/%s/collection.json' % collection_id
    collection = json.load(open(atcity(collection_file)))
    logging.info('found %d models in the collection' % len(collection['vehicles']))

    exportCollection(cursor, collection)

  conn.commit()
  