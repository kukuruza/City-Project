import os, os.path as op
import re
import shutil
import time
import fnmatch


def _find_files_ (directory, pattern):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename

if not os.environ.get('CITY_DATA_PATH'):
    raise Exception ('Set environmental variables CITY_DATA_PATH')

rootdir = os.getenv('CITY_DATA_PATH')
backupdir = op.join (os.getenv('CITY_PATH'), 'backup-db-%s' % time.strftime('%Y-%m-%d'))

for in_db_path in _find_files_ (rootdir, '*.db'):
    
    in_db_dir = op.dirname(in_db_path)
    out_db_dir = op.join(backupdir, op.relpath(in_db_dir, rootdir))

    print 'from %s' % in_db_path
    print 'to   %s' % op.join(out_db_dir, op.basename(in_db_path))

    if not op.exists(out_db_dir):
        os.makedirs (out_db_dir)
    shutil.copy(in_db_path, op.join(out_db_dir, op.basename(in_db_path)))

