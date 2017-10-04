import sys, os, os.path as op
import argparse
import logging, logging.handlers
import shutil
import sqlite3


def print_to_tqdm(t, msg, msg_len=50):
  msg = msg.ljust(msg_len)
  t.set_description(msg)
  t.refresh()


def atcity (path):
  if op.isabs(path):
    return path
  else:
    if not os.getenv('CITY_PATH'):
        raise Exception ('Please set environmental variable CITY_PATH')
    return op.join(os.getenv('CITY_PATH'), path)


def atcitydata (path):
  if op.isabs(path):
    return path
  else:
    if not os.getenv('CITY_DATA_PATH'):
      raise Exception ('Please set environmental variable CITY_DATA_PATH')
    return op.join(os.getenv('CITY_DATA_PATH'), path)


def setupLogHeader (db_in_path, db_out_path, params, name):
    ''' Highest level scripts use it '''
    logging.info ('=== processing %s ===' % name)
    logging.info ('db_in_path:  %s' % db_in_path)
    logging.info ('db_out_path: %s' % db_out_path)
    logging.info ('params:      %s' % str(params))


def _setupCopyDb_ (in_path, out_path):
    ''' 
    First in_path is copied into out_path, which is backed-up if exists. 
    All modifications are then done on out_path. 
    in_path will never be modified later whatever bugs happen
    '''
    if not op.exists (in_path):
        raise Exception ('db does not exist: %s' % in_path)
    if op.exists (out_path):
        logging.warning ('will back up existing out_path')
        backup_path = out_path + '.backup'
        if in_path != out_path:
            if op.exists (backup_path): os.remove (backup_path)
            os.rename (out_path, backup_path)
        else:
            shutil.copyfile(in_path, backup_path)
    if in_path != out_path:
        # copy input database into the output one
        shutil.copyfile(in_path, out_path)


def setParamUnlessThere (params, key, default):
    if not key in params: 
        params[key] = default
        logging.debug ('setParamUnlessThere set %s to its default.' % key)
    else:
        logging.debug ('setParamUnlessThere found %s in params.' % key)



def assertParamIsThere (params, key):
    if not key in params.keys():
        raise Exception ('Key "%s" should be in "params"' % key)


def setupLogging (filename, level=logging.INFO, filemode='w'):
    log = logging.getLogger('')
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s: \t%(message)s')
    log.setLevel(logging.DEBUG)

    log_path = atcity(filename)
    if not op.exists (op.dirname(log_path)):
        os.makedirs (op.dirname(log_path))
    fh = logging.handlers.RotatingFileHandler(log_path, mode=filemode)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    sh.setLevel(level)
    log.addHandler(sh)



def dbInit (db_in_path, db_out_path=None, backup=True):
    '''
    The function knows about CITY_DATA_PATH and CITY_PATH.
    It also sets up logging, backs up the database if necessary.
    '''
    logging.info ('db_in_file:  %s' % db_in_path)
    logging.info ('db_out_file: %s' % db_out_path)

    db_in_path  = atcity(db_in_path)
    db_out_path = atcity(db_out_path) if db_out_path else db_in_path

    if backup or db_in_path != db_out_path:
        _setupCopyDb_ (db_in_path, db_out_path)

    assert op.exists(db_out_path), db_out_path
    conn = sqlite3.connect (db_out_path)
    cursor = conn.cursor()
    return (conn, cursor)
