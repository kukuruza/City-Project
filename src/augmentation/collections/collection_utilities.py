import os, os.path as op
import logging
from shutil import copyfile

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


def atcity (path):
  if path == ':memory:':
    return ':memory:'
  elif op.isabs(path):
    return path
  else:
    if not os.getenv('CITY_PATH'):
        raise Exception ('Please set environmental variable CITY_PATH')
    return op.join(os.getenv('CITY_PATH'), path)
