import sys, os, os.path as op
import logging, logging.handlers
import shutil



def setupLogHeader (db_in_path, db_out_path, params, name):
    logging.info ('=== processing ' + name + '===')
    logging.info ('db_in_path:  ' + db_in_path)
    logging.info ('db_out_path: ' + db_out_path)
    logging.info ('params:      ' + str(params))


def setupCopyDb (db_in_path, db_out_path):
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
    if not key in params.keys(): params[key] = default_value
    return params


def assertParamIsThere (params, key):
    if not key in params.keys():
        raise Exception ('key %s is not in params' % key)


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


def get_CITY_DATA_PATH():
    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        raise Exception ('Set environmental variables CITY_PATH, CITY_DATA_PATH')
    return os.getenv('CITY_DATA_PATH')


