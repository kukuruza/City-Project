#!/usr/bin/python
#
# This script is for exploring distributions of car attributes
#

import logging, logging.handlers
import os, sys
import os.path as op
import shutil
import glob
import json
import numpy
import sqlite3
import Gnuplot, Gnuplot.funcutils, Gnuplot.PlotItems


if __name__ == '__main__':

    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        raise Exception ('Set environmental variables CITY_PATH, CITY_DATA_PATH')

    log = logging.getLogger('')
    log.setLevel (logging.INFO)
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s: \t%(message)s')
    log_path = op.join (os.getenv('CITY_PATH'), 'log/learning/getDistribution.log')
    fh = logging.handlers.RotatingFileHandler(log_path, mode='w')
    fh.setFormatter(formatter)
    log.addHandler(fh)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    log.addHandler(sh)
 

    if len(sys.argv) <= 2:
        print 'Please pass the db path and a query string as arguments'
        sys.exit()

    db_path = op.join (os.getenv('CITY_DATA_PATH'), sys.argv[1])
    logging.info ('db path: ' + db_path)

    if not op.exists (db_path):
        raise Exception ('db does not exist: ' + db_path)


    conn = sqlite3.connect (db_path)
    cursor = conn.cursor()

    query_str = ' '.join(sys.argv[2:])
    print ('query: ' + query_str)
    cursor.execute(query_str)
    response = cursor.fetchall()
    data = [list(row) for row in response]

    conn.close()

    # prase query string for labels
    query_list = map(lambda x:x.lower(), query_str.replace(',', ' ').split())
    index_select = query_list.index('select')
    index_from   = query_list.index('from')
    labels       = query_list[index_select+1:index_from]
    
    if not data: 
        print ('nothing was found for this query.')
        sys.exit()

    assert (len(labels) == len(data[0]))
    g = Gnuplot.Gnuplot(debug=1)
    g.title(query_str + ' (' + str(len(data)) + ' points)')
    if len(labels) == 2:
        g.xlabel (labels[0])
        g.ylabel (labels[1])

    g.plot(data)

