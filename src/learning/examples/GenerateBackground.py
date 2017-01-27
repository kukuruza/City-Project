import os, sys, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import logging
from learning.helperSetup import setupLogging, dbInit
from learning.dbModify import generateBackground


setupLogging ('log/learning/Manually.log', logging.INFO, 'a')

in_db_file  = 'databases/idatafa/572-Feb23-09h/train-Jan26/forback-part.db'
out_db_file = 'databases/idatafa/572-Feb23-09h/train-Jan26/back-part.db'
out_videofile = 'camdata/cam572/Feb23-09h/back-part.avi'


(conn, cursor) = dbInit(in_db_file, out_db_file)
generateBackground (cursor, out_videofile, params={'show_debug': False, 'dilate_radius': 2})
conn.commit()
conn.close()

