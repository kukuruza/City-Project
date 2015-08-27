import logging
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning/labelme'))
import helperSetup
import labelme2db
 

helperSetup.setupLogging ('log/learning/Labelme2dbPairs.log', logging.INFO, 'a')

db_in_path  = 'datasets/labelme/Databases/572-Nov28-10h-pair/init.db'
db_out_path = 'datasets/labelme/Databases/572-Nov28-10h-pair/parsed.db'

params = { 'debug_show': False }

(conn, cursor) = helperSetup.dbInit(db_in_path, db_out_path)
labelme2db.folder2pairs (cursor, params)
conn.commit()
conn.close()
