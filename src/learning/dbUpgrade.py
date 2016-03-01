import logging
import os, sys, os.path as op
from helperSetup import setupLogging, _setupCopyDb_, dbInit
import sqlite3
import shutil
import traceback
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



def upgrade4 (c, in_db_path):
    '''
    Before 2016-Feb-28, videos were stored as follows:
      cam124 -> [Feb28-10h.avi, Feb28-10h-mask.avi, ..., Feb28-10h.txt]
    Since 2016-Feb-28, videos are stored as follows:
      cam124 -> Feb28-10h -> [src.avi, mask.avi, ghost.avi, back.avi, time.avi]
    This file updates the db imagefile and maskfile entries.
    Also extension is removed from imagefile and maskfile, where videos are used
    '''
    c.execute('SELECT imagefile,maskfile FROM images')
    for (old_imagefile, old_maskfile) in c.fetchall():

        db_name = op.splitext(op.basename(in_db_path))[0]
        if db_name[-5:] == 'ghost':

            # find the last dash "-" in pattern mydir/mydb-ghost/000000.jpg
            index = old_imagefile.rfind('-')
            assert old_imagefile[index+1:index+6] == 'ghost', old_imagefile
            new_imagefile = old_imagefile[:index] + '/' + old_imagefile[index+1:]

        elif db_name[-4:] == 'back':

            # find the last dash "-" in pattern mydir/mydb-back/000000.jpg
            index = old_imagefile.rfind('-')
            assert old_imagefile[index+1:index+5] == 'back', old_imagefile
            new_imagefile = old_imagefile[:index] + '/' + old_imagefile[index+1:]

        else: # src video

            # find the last slash "/" in pattern mydir/mydb/000000.jpg
            index = old_imagefile.rfind('/')
            assert old_imagefile[index-5:index] != 'ghost', old_imagefile[index-5:index]
            new_imagefile = old_imagefile[:index] + '/src' + old_imagefile[index:]

        # find the last dash in pattern mydir/mydb-ghost/000000.jpg
        index = old_maskfile.rfind('-')
        new_maskfile = old_maskfile[:index] + '/' + old_maskfile[index+1:]
        # remove the extension
        new_maskfile = op.splitext(new_maskfile)[0]

        # remove the extension
        new_imagefile = op.splitext(new_imagefile)[0]

        c.execute('UPDATE images SET maskfile=?  WHERE imagefile=?', (new_maskfile,  old_imagefile))
        c.execute('UPDATE images SET imagefile=? WHERE imagefile=?', (new_imagefile, old_imagefile))
        c.execute('UPDATE cars   SET imagefile=? WHERE imagefile=?', (new_imagefile, old_imagefile))


if __name__ == '__main__':
    setupLogging ('log/learning/UpgradeDb.log', logging.WARNING, 'a')
    path = op.join(os.getenv('CITY_DATA_PATH'), 'databases/unlabelled')
    for db_in_path in _find_files_ (path, '*.db'):
        try:
            conn = sqlite3.connect (db_in_path)
            upgrade4 (conn.cursor(), db_in_path)
            conn.commit()
            conn.close()
        except:
            logging.error('file %s failed to be processed: %s' % \
                          (db_in_path, traceback.format_exc()))


    # db_in_path = op.join(os.getenv('CITY_DATA_PATH'), 'databases/augmentation/Apr07-15h-traffic.db')
    # db_out_path = op.join(os.getenv('CITY_DATA_PATH'), 'databases/augmentation/Apr07-15h-traffic.new.db')
    # (conn, cursor) = dbInit(db_in_path, db_out_path)
    # upgrade4 (cursor, db_in_path)
    # conn.commit()
    # conn.close()
