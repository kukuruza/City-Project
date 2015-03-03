#!/usr/bin/python
#
# This script is for exploring distributions of car attributes
#   It can talk to the database made by cars2db
#

import sqlite3
import logging
import os, sys
import os.path as OP
import shutil
import glob
import json
import numpy, cv2
import Gnuplot, Gnuplot.funcutils, Gnuplot.PlotItems


if not os.environ.get('CITY_PATH'):
    print 'First set the environmental variable CITY_PATH'
    sys.exit()
else:
    sys.path.insert(0, OP.join(os.getenv('CITY_PATH'), 'src'))

from pycar.pycar import Car, loadMatCars



def queryDb (db_path, query_string):

    conn = sqlite3.connect (db_path)
    c = conn.cursor()
    return c.execute(query_string)


if __name__ == '__main__':
    ''' Demo '''

    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        print 'First set the environmental variable CITY_PATH, CITY_DATA_PATH'
        sys.exit()
    else:
        CITY_PATH = os.getenv('CITY_PATH')
        CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')

    FORMAT = '%(asctime)s %(levelname)s: \t%(message)s'
    log_path = OP.join (CITY_PATH, 'log/learning/getDistribution.log')
    logging.basicConfig (format=FORMAT, filename=log_path, level=logging.DEBUG)

    clusters_root = OP.join (CITY_DATA_PATH, 'clustering')

    db_path = OP.join (clusters_root, 'attributes.db')

    if len(sys.argv) <= 1:
        print 'Please pass a query string as an argument'
        sys.exit()

    query_string = ' '.join(sys.argv[1:])
    print ('querying ' + query_string)
    response = queryDb(db_path, query_string)
    data = [list(row) for row in response]

    # prase query string for labels
    query_list = map(lambda x:x.lower(), query_string.split())
    index_select = query_list.index('select')
    index_from   = query_list.index('from')
    labels       = query_list[index_select+1:index_from]
    
    if not data: 
        print ('nothing was found for this query.')
        sys.exit()

    assert (len(labels) == len(data[0]))
    g = Gnuplot.Gnuplot(debug=1)
    g.title(query_string + ' (' + str(len(data)) + ' points)')
    if len(labels) == 2:
        g.xlabel (labels[0])
        g.ylabel (labels[1])

    g.plot(data)

