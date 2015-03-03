#!/usr/bin/python
#
# This module assmebles car properties into a database.
#   That database can be used for clustering, examining ditribution, etc
#

import sqlite3
import logging
import os, sys
import os.path as OP
import shutil
import glob
import json
import numpy, cv2

if not os.environ.get('CITY_PATH'):
    print 'First set the environmental variable CITY_PATH'
    sys.exit()
else:
    sys.path.insert(0, OP.join(os.getenv('CITY_PATH'), 'src'))

from pycar.pycar import Car, loadMatCars



def createDb (data_paths_list, db_path):

    if OP.exists (db_path):
        os.remove (db_path)

    conn = sqlite3.connect (db_path)

    c = conn.cursor()

    c.execute('''CREATE TABLE cars
                 (filepath text, 
                  objectindex integer, 
                  name text, 
                  width integer, 
                  height integer,
                  size integer,
                  yaw real,
                  pitch real
                  )''')

    # go through directories one by one
    for data_path_template in data_paths_list:
        logging.debug ('createDb looks for template: ' + data_path_template)

        # the list probably contains wildcards
        data_paths = glob.glob (data_path_template)
        logging.info ('createDb found ' + str(len(data_paths)) + \
            ' objects at template path: ' + data_path_template)
        for data_path in data_paths:
            logging.debug ('createDb looks for objects in: ' + data_path)

            cars = loadMatCars (data_path)
            for i in range(len(cars)):
                car = cars[i]

                # skip empty cars
                if not car.isOk(): continue

                # make an entry and enter into database
                entry = (data_path,
                         i, 
                         car.name, 
                         car.width,
                         car.height,
                         car.size,
                         car.yaw,
                         car.pitch)

                c.execute('INSERT INTO cars VALUES (?,?,?,?,?,?,?,?)', entry)

    conn.commit()
    conn.close()



if __name__ == '__main__':
    ''' Demo '''

    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        print 'First set the environmental variable CITY_PATH, CITY_DATA_PATH'
        sys.exit()
    else:
        CITY_PATH = os.getenv('CITY_PATH')
        CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')

    FORMAT = '%(asctime)s %(levelname)s: \t%(message)s'
    log_path = OP.join (CITY_PATH, 'log/learning/cars2db.log')
    logging.basicConfig (format=FORMAT, filename=log_path, level=logging.DEBUG)

    clusters_root = OP.join (CITY_DATA_PATH, 'clustering')

    data_list_path = OP.join (clusters_root, 'data.list')
    if not os.path.exists(data_list_path):
        raise Exception('data_list_path does not exist: ' + data_list_path)
    data_list_file = open(data_list_path, 'r')
    data_list = data_list_file.read().split('\n')
    data_list_file.close()
    # remove empty lines
    data_list = filter(None, data_list)
    # make it relative to the data_list_path
    data_list = [OP.join(CITY_DATA_PATH, x) for x in data_list]

    db_path = OP.join (clusters_root, 'attributes.db')

    createDb (data_list, db_path)

