import os, os.path as op
import logging
from shutil import copyfile
import sqlite3


def atcity (path):
  if path == ':memory:':
    return ':memory:'
  elif op.isabs(path):
    return path
  else:
    if not os.getenv('CITY_PATH'):
        raise Exception ('Please set environmental variable CITY_PATH')
    return op.join(os.getenv('CITY_PATH'), path)


WORK_DIR = atcity('data/augmentation/blender/current-collection')


def getExamplePath(collection_id, model_id):
  example_path = atcity(op.join('data/augmentation/CAD/%s/examples/%s.png' %
      (collection_id, model_id)))
  assert op.exists(op.dirname(example_path)), 'Dir of %s must exist' % example_path
  return example_path


def getBlendPath(collection_id, model_id):
  blend_path = atcity(op.join('data/augmentation/CAD/%s/blend/%s.blend' %
      (collection_id, model_id)))
  assert op.exists(op.dirname(blend_path)), 'Dir of %s must exist' % blend_path
  return blend_path


def safeConnect (in_path, out_path):
  '''
  Connect to Sqlite3 db with backing up.
  Copy in_path into out_path, which is backed-up if exists.
  In-memory databases are processed separately.
  '''

  if out_path == ':memory:' and not op.exists (in_path):
    return sqlite3.connect(':memory:')
  
  elif out_path == ':memory:' and op.exists (in_path):
    in_conn  = sqlite3.connect(in_path)
    out_conn = sqlite3.connect(':memory:')
    # Copy from disk to memory.
    query = ''.join(line for line in in_conn.iterdump())
    out_conn.executescript(query)
    in_conn.close()
    return out_conn

  if not op.exists (in_path):
    raise Exception ('in db does not exist: %s' % in_path)

  if op.exists (out_path):
    logging.warning ('will back up existing out_path')
    ext = op.splitext(out_path)[1]
    backup_path = op.splitext(out_path)[0]  + '.backup%s' % ext
    if in_path != out_path:
      if op.exists (backup_path):
        os.remove (backup_path)
      os.rename (out_path, backup_path)
    else:
      copyfile(in_path, backup_path)

  if in_path != out_path:
    # copy input database into the output one
    copyfile(in_path, out_path)

  return sqlite3.connect(out_path)


def safeCopy (in_path, out_path):
  '''Copy in_path into out_path, which is backed-up if exists.'''

  if out_path == ':memory:':
    return
  if not op.exists (in_path):
    raise Exception ('db does not exist: %s' % in_path)
  if op.exists (out_path):
    logging.warning ('will back up existing out_path')
    ext = op.splitext(out_path)[1]
    backup_path = op.splitext(out_path)[0]  + '.backup%s' % ext
    if in_path != out_path:
      if op.exists (backup_path):
        os.remove (backup_path)
      os.rename (out_path, backup_path)
    else:
      copyfile(in_path, backup_path)
  if in_path != out_path:
    # copy input database into the output one
    copyfile(in_path, out_path)

def backupFile(in_path, out_path):
  if not op.exists (in_path):
    raise Exception ('File does not exist: %s' % in_path)
  if op.exists (out_path):
    logging.warning ('Will back up existing out_path: %s' % out_path)
    backup_path = '%s.backup.%s' % op.splitext(out_path)
    if in_path != out_path:
      if op.exists (backup_path):
        os.remove (backup_path)
      os.rename (out_path, backup_path)
    else:
      copyfile(in_path, backup_path)
  if in_path != out_path:
    # copy input database into the output one
    copyfile(in_path, out_path)


def deleteAbsoleteFields(vehicle):
  '''
  Remove fields of collection.json that are absolete and clutter the space.
  Scripts should call this function besides their main function. 
  '''
  if 'blend_file' in vehicle:
    del vehicle['blend_file']
