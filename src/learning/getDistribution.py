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
from argparse import ArgumentParser


def getSrcMap (cursor):
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT src FROM images')
    entries = cursor.fetchall()
    entries = [e for (e,) in entries]
    return dict(zip(entries, range(len(entries))))



if __name__ == '__main__':

    parser = ArgumentParser(description='check geometry maps')
    parser.add_argument('--db_path', type=str, required=True, help='path to a .db')
    parser.add_argument('--tmp_path', type=str, help='path to the temporary tmp.scv file')
    parser.add_argument('--legend_path', type=str, help='path to the legend file')
    parser.add_argument('--query', type=str, required=True, 
                        help='SQL query in the form: "SELECT ... WHERE ... "')
    args = parser.parse_args()

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
 
    db_path = op.join (os.getenv('CITY_DATA_PATH'), args.db_path)
    logging.info ('db path: ' + db_path)

    if not op.exists (db_path):
        raise Exception ('db does not exist: ' + db_path)


    conn = sqlite3.connect (db_path)
    cursor = conn.cursor()
    srcMap = getSrcMap (cursor)

    query_str = args.query
    print ('query string: \n' + query_str)
    cursor.execute(query_str)
    response = cursor.fetchall()
    data = [list(row) for row in response]

    conn.close()

    # phrase query string for labels
    query_list = map(lambda x:x.lower(), query_str.replace(',', ' ').split())
    index_select = query_list.index('select')
    index_from   = query_list.index('from')
    labels       = query_list[index_select+1:index_from]

    if not data: 
        print ('nothing was found for this query.')
        sys.exit()

    if args.tmp_path:
        with open(args.tmp_path, 'w') as f:
            #f.write (str(labels[0]) + ',' + str(labels[1]) + ',color \n')
            for entry in data:
                f.write (str(entry[0]) + ',' + str(entry[1]) + ',' + str(srcMap[entry[2]]) + '\n')

    if args.legend_path:
        with open(args.legend_path, 'w') as f:
            for item in srcMap.iteritems():
                f.write (str(item[0]) + ' ' + str(item[1]) + '\n')

    
    #assert (len(labels) == len(data[0]))
    #g = Gnuplot.Gnuplot(debug=1)
    #g.title(query_str + ' (' + str(len(data)) + ' points)')
    #if len(labels) == 2:
    #    g.xlabel (labels[0])
    #    g.ylabel (labels[1])
    #g.plot(data)

