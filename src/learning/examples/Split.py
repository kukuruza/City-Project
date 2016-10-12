import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
from learning.helperSetup import setupLogging, dbInit
from learning.dbModify    import splitToRandomSets


setupLogging ('log/learning/Split.log', logging.INFO, 'a')

in_db_file = 'augmentation/video/cam572/Feb23-09h-406fr/traffic.db'

(conn, cursor) = dbInit(in_db_file)
db_out_names = {'test2': 0.005}

splitToRandomSets (cursor, os.path.dirname(in_db_file), db_out_names)

conn.close()
