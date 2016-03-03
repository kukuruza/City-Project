import os, sys, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import logging
from learning.helperSetup import setupLogging, dbInit
from learning.dbModify import filterByBorder, expandBboxes


setupLogging ('log/learning/Modify.log', logging.INFO, 'a')

in_db_file  = 'databases/sparse/all-Feb29.db'
out_db_file = 'databases/sparse/all-Feb29-wr-wb.db'

(conn, cursor) = dbInit (in_db_file, out_db_file)
filterByBorder (cursor)
expandBboxes (cursor, params={'expand_perc': 0})
conn.commit()
conn.close()
