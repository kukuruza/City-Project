import logging
import os, sys, os.path as op
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
from helperSetup import setupLogging, _setupCopyDb_
import sqlite3
import shutil
import fnmatch
import helperDb


def _find_files_ (directory, pattern):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename


def upgrade3 (c_image, c_ghost):

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

    fixVer2_1 (c_image)
    fixVer2_1 (c_ghost)


def upgrade3_paths (db_in_path):

    logging.info ('db_in_path: %s' % db_in_path)

    # check that it's not the new file
    #conn0 = sqlite3.connect (db_in_path)
    #version = conn0.execute('PRAGMA user_version').fetchone()
    #conn0.close()
    #if version is not None and version[0] == 2: 
    #    logging.info ('db is already upgraded to version 2')
    #    return

    db_image_path = op.splitext(db_in_path)[0] + '-image.db'
    db_ghost_path = op.splitext(db_in_path)[0] + '-ghost.db'
    logging.info ('db_image_path: %s' % db_image_path)
    logging.info ('db_ghost_path: %s' % db_ghost_path)

    shutil.copy(db_in_path, db_image_path)
    shutil.copy(db_in_path, db_ghost_path)
    os.remove(db_in_path)

    conn_image = sqlite3.connect (db_image_path)
    conn_ghost = sqlite3.connect (db_ghost_path)

    try:
        upgrade3 (conn_image.cursor(), conn_ghost.cursor())
    except Exception():
        logging.error ('failed to upgrade %s' % db_in_path)

    conn_image.commit()
    conn_ghost.commit()

    conn_image.close()
    conn_ghost.close()



def fixVer2_1 (c):

    helperDb.createTableMatches(c)

    c.execute('SELECT imagefile FROM images')
    truefiles = c.fetchall()
    truenames = [op.basename(x[0]) for x in truefiles]

    c.execute('SELECT id,imagefile FROM cars')
    for (carid,imagefile) in c.fetchall():

        imagename = op.basename(imagefile)
        if imagename not in truenames:
            logging.error ('imagename %s not in truenames' % imagename)
            raise Exception()

        index = truenames.index(imagename)
        c.execute('UPDATE cars SET imagefile=? WHERE id=?', (truefiles[index][0], carid))

    c.execute('PRAGMA user_version = 3')



def fixVer2_1_path (db_in_path):

    #_setupCopyDb_ (db_in_path, db_in_path)

    logging.info ('db_in_path: %s' % db_in_path)

    # check that it's not the new file
    conn = sqlite3.connect (db_in_path)
    version = conn.execute('PRAGMA user_version').fetchone()
    if version is not None and version[0] == 3: 
        logging.warning ('db is already upgraded to version 3')
        return
    
    try:
        fixVer2_1(conn.cursor())
    except Exception:
        logging.error ('Exception in file: %s' % db_in_path)

    conn.commit()
    conn.close()


if __name__ == '__main__':
    setupLogging ('log/learning/UpgradeDb.log', logging.WARNING, 'a')
    path = os.getenv('CITY_DATA_PATH')
    for db_in_path in _find_files_ (path, '*.db.backup'):
        upgrade3_paths (db_in_path)
    #upgrade3_paths (op.join(os.getenv('CITY_DATA_PATH'), 'databases/572-578-e0.1.db'))
