import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
from learning.helperSetup         import setupLogging, dbInit
from learning.labelme.labelme2db  import folder2frames
from learning.dbModify            import polygonsToMasks
 

setupLogging ('log/learning/Labelme2dbFrames.log', logging.INFO, 'a')

#db_in_file  = 'databases/labelme/164-Feb23-09h/init-image.db'
db_in_file  = 'databases/labelme/572-Jan13-10h/src-test.db'
db_out_file = 'databases/labelme/572-Jan13-10h/parsed-test.db'
annotations_dir = 'databases/labelme/572-Jan13-10h/xml'

params = { 'debug_show': False }

(conn, cursor) = dbInit(db_in_file, db_out_file)
folder2frames (cursor, annotations_dir, params)
#polygonsToMasks (cursor)
conn.commit()
conn.close()
