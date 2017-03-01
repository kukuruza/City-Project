#! /usr/bin/env python
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup import setupLogging, dbInit
from learning.dbCnn       import DbCnn


parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--out_db_file', required=True)
parser.add_argument('--model_file', required=True,
        help='e.g. cnn/models/vehicle_iter_20000.caffemodel')
parser.add_argument('--network_file', required=True,
        help='e.g. cnn/architectures/vehicle-deploy-py.prototxt')
parser.add_argument('--logging_level', default=20, type=int)
args = parser.parse_args()


setupLogging ('log/learning/Filter.log', args.logging_level, 'a')

(conn, cursor) = dbInit(args.in_db_file, args.out_db_file)
dbCnn = DbCnn(args.network_file, args.model_file)
dbCnn.classify(cursor, {'label_dict': {0: 'negative', 1: 'vehicle'}, 
                        'resize': (40, 30)})
conn.commit()
conn.close()
