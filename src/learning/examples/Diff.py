import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup import setupLogging, dbInit
from learning.dbModify    import diffImagefiles


parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--ref_db_file', required=True)
parser.add_argument('--out_db_file', required=True)
parser.add_argument('--logging_level', default=20, type=int)
args = parser.parse_args()

setupLogging ('log/learning/Diff.log', args.logging_level, 'a')

(conn, cursor) = dbInit(args.in_db_file, args.out_db_file)
(conn_ref, cursor_ref) = dbInit(args.ref_db_file, backup=False)
diffImagefiles (cursor, cursor_ref)

conn.commit()
conn.close()
conn_ref.close()

