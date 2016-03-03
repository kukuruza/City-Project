import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
from learning.helperSetup import setupLogging, dbInit
from learning.dbManual    import show


setupLogging ('log/learning/Manually.log', logging.INFO, 'a')

db_in_file = 'databases/sparse/all-Feb29.db'

(conn, cursor) = dbInit(db_in_file, backup=False)
show(cursor, params={})
conn.close()
