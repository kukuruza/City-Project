import logging
import os, sys, os.path as op
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
from helperSetup import setupLogging
import sqlite3
import shutil
import fnmatch


def _find_files_ (directory, pattern):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename


def upgrade2 (c_image, c_ghost):

    c_image.execute('PRAGMA user_version = 2')
    c_image.execute('CREATE TEMPORARY TABLE backup(imagefile,src,width,height,maskfile,time)')
    c_image.execute('INSERT INTO backup SELECT imagefile,src,width,height,maskfile,time FROM images')
    c_image.execute('DROP TABLE images')
    c_image.execute('CREATE TABLE images(imagefile,src,width,height,maskfile,time)')
    c_image.execute('INSERT INTO images SELECT imagefile,src,width,height,maskfile,time FROM backup')
    c_image.execute('DROP TABLE backup')

    c_ghost.execute('PRAGMA user_version = 2')
    c_ghost.execute('CREATE TEMPORARY TABLE backup(ghostfile,src,width,height,maskfile,time)')
    c_ghost.execute('INSERT INTO backup SELECT ghostfile,src,width,height,maskfile,time FROM images')
    c_ghost.execute('DROP TABLE images')
    c_ghost.execute('CREATE TABLE images(imagefile,src,width,height,maskfile,time)')
    c_ghost.execute('INSERT INTO images SELECT ghostfile,src,width,height,maskfile,time FROM backup')
    c_ghost.execute('DROP TABLE backup')


def upgrade2_paths (db_in_path):

    logging.info ('db_in_path: %s' % db_in_path)

    # check that it's not the new file
    conn0 = sqlite3.connect (db_in_path)
    version = conn0.execute('PRAGMA user_version').fetchone()
    conn0.close()
    if version is not None and version[0] == 2: 
        logging.info ('db is already upgraded to version 2')
        return

    db_image_path = op.splitext(db_in_path)[0] + '-image.db'
    db_ghost_path = op.splitext(db_in_path)[0] + '-ghost.db'
    logging.info ('db_image_path: %s' % db_image_path)
    logging.info ('db_ghost_path: %s' % db_ghost_path)

    shutil.copy(db_in_path, db_image_path)
    shutil.copy(db_in_path, db_ghost_path)
    os.remove(db_in_path)

    conn_image = sqlite3.connect (db_image_path)
    conn_ghost = sqlite3.connect (db_ghost_path)

    upgrade2 (conn_image.cursor(), conn_ghost.cursor())

    conn_image.commit()
    conn_ghost.commit()

    conn_image.close()
    conn_ghost.close()


if __name__ == '__main__':
    setupLogging ('log/learning/UpgradeDb.log', logging.INFO, 'a')
    #path = '/Users/evg/projects/City-Project/data/datasets/sparse/Databases/119-Apr09-13h-copy'
    path = os.getenv('CITY_DATA_PATH')
    for db_in_path in _find_files_ (path, '*.db'):
        upgrade2_paths (db_in_path)

