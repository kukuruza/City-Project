import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
from learning.helperSetup        import setupLogging, dbInit
from learning.labelme.labelme2db import folder2pairs
 

setupLogging ('log/learning/Labelme2dbPairs.log', logging.INFO, 'a')

db_in_file  = 'databases/labelme/572-Nov28-10h-pair/init.db'
db_out_file = 'databases/labelme/572-Nov28-10h-pair/parsed.db'

params = { 'debug_show': False }

(conn, cursor) = dbInit(db_in_file, db_out_file)
folder2pairs (cursor, params)
conn.commit()
conn.close()
