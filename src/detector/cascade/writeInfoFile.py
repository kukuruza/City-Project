import logging, logging.handlers
import shutil
import glob
import json
import sqlite3
import sys
import os, os.path as op
sys.path.insert(0, os.path.abspath('../../learning'))
from dbInterface import queryCars, queryField


if __name__ == '__main__':

    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        raise Exception ('Set environmental variables CITY_PATH, CITY_DATA_PATH')
    CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')

    log = logging.getLogger('')
    log.setLevel (logging.INFO)
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s: \t%(message)s')
    log_path = op.join (os.getenv('CITY_PATH'), 'log/detector/writeInfoFile.log')
    fh = logging.handlers.RotatingFileHandler(log_path, mode='w')
    fh.setFormatter(formatter)
    log.addHandler(fh)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    log.addHandler(sh)

    db_path      = op.join (CITY_DATA_PATH, 'databases/wratio-wborder.db')
    filters_path = op.join (CITY_DATA_PATH, 'clustering/cars_by_size/clusters.json')
    info_dir     = op.join (CITY_DATA_PATH, 'violajones/cars_by_size')

    # open db
    if not op.exists (db_path):
        raise Exception ('db does not exist: ' + db_path)
    conn = sqlite3.connect (db_path)
    cursor = conn.cursor()

    # load clusters
    if not op.exists(filters_path):
        raise Exception('filters_path does not exist: ' + filters_path)
    filters_file = open(filters_path)
    filters_groups = json.load(filters_file)
    filters_file.close()

    # delete 'info_dir' dir, and recreate it
    if op.exists (info_dir):
        shutil.rmtree (info_dir)
    os.makedirs (info_dir)

    for filter_group in filters_groups:
        assert ('filter' in filter_group)

        info_file = open(op.join(info_dir, filter_group['filter'] + '.info'), 'w')

        cursor.execute('SELECT imagefile FROM images')
        imagefiles = cursor.fetchall()

        for (imagefile,) in imagefiles:

            # get db entries
            filter_group['imagefile'] = imagefile
            car_entries = queryCars (cursor, filter_group)

            info_file.write (imagefile + ' ' + str(len(car_entries)))

            for car_entry in car_entries:
                bbox = queryField(car_entry, 'bbox-w-offset')
                info_file.write ('   ' + ' '.join(str(e) for e in bbox))

            info_file.write('\n')

    info_file.close()
    conn.close()


