import sys, os, os.path as op
import logging, logging.handlers
import shutil
import sqlite3


'''
Everything one may need to process a database.
The main interface functions are dbInit(), setParamUnlessThere(), assertParamIsThere()
'''


def setupLogHeader (db_in_path, db_out_path, params, name):
    ''' Highest level scripts use it '''
    logging.info ('=== processing %s ===' % name)
    logging.info ('db_in_path:  %s' % db_in_path)
    logging.info ('db_out_path: %s' % db_out_path)
    logging.info ('params:      %s' % str(params))


def _setupCopyDb_ (db_in_path, db_out_path):
    ''' 
    First db_in_path is copied into db_out_path, which is backed-up if exists. 
    All modifications are then done on db_out_path. 
    db_in_path will never be modified later whatever bugs happen
    '''
    if not op.exists (db_in_path):
        raise Exception ('db does not exist: ' + db_in_path)
    if op.exists (db_out_path):
        logging.warning ('will back up existing db_out_path')
        backup_path = db_out_path + '.backup'
        if db_in_path != db_out_path:
            if op.exists (backup_path): os.remove (backup_path)
            os.rename (db_out_path, backup_path)
        else:
            shutil.copyfile(db_in_path, backup_path)
    if db_in_path != db_out_path:
        # copy input database into the output one
        shutil.copyfile(db_in_path, db_out_path)


def setParamUnlessThere (params, key, default_value):
    if not key in params: params[key] = default_value


def assertParamIsThere (params, key):
    if not key in params.keys():
        raise Exception ('Key "%s" should be in "params"' % key)


def setupLogging (filename, level=logging.INFO, filemode='w'):
    log = logging.getLogger('')
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s: \t%(message)s')
    log.setLevel(level)

    log_path = os.path.join (os.getenv('CITY_PATH'), filename)
    if not op.exists (op.dirname(log_path)):
        os.makedirs (op.dirname(log_path))
    fh = logging.handlers.RotatingFileHandler(log_path, mode=filemode)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    log.addHandler(sh)


def dbInit (db_in_path, db_out_path = None):
    '''
    The function knows about CITY_DATA_PATH and CITY_PATH.
    It also sets up logging, backs up the database if necessary.
    '''

    if not os.getenv('CITY_DATA_PATH') or not os.getenv('CITY_PATH'):
        raise Exception ('Set environmental variables CITY_PATH, CITY_DATA_PATH')

    logging.info ('db_in_path:  ' + str(db_in_path))
    logging.info ('db_out_path: ' + str(db_out_path))

    CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')
    db_in_path  = op.join (CITY_DATA_PATH, db_in_path)
    db_out_path = op.join (CITY_DATA_PATH, db_out_path) if db_out_path else db_in_path

    _setupCopyDb_ (db_in_path, db_out_path)

    conn = sqlite3.connect (db_out_path)
    cursor = conn.cursor()
    return (conn, cursor)