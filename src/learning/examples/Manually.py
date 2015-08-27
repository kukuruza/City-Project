import logging
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
import helperSetup
import dbManual

helperSetup.setupLogging ('log/learning/Manually.log', logging.INFO, 'a')

db_in_path =  'datasets/labelme/Databases/572-Nov28-10h-pair/detected/ex0.1-di0.3-er0.3-filt.db'

(conn, cursor) = helperSetup.dbInit(db_in_path, db_out_path)
dbManual.labelMatches()
conn.close()
