import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from pprint import pprint
from learning.helperSetup import setupLogging, dbInit
from learning.dbManual    import getInfo


parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--logging_level', default=20, type=int)
args = parser.parse_args()

setupLogging ('log/learning/Info.log', args.logging_level, 'a')

(conn, cursor) = dbInit(args.in_db_file, backup=False)
info = getInfo(cursor, params={})
pprint (info)

#cursor.execute('SELECT COUNT(*) FROM cars WHERE width >= 25')
#print cursor.fetchone()

conn.close()

