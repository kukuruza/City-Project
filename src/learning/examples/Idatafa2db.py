import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
from learning.helperSetup         import setupLogging, dbInit
from learning.labelme.idatafa2db  import folder2frames, filterDbWithList
from learning.dbModify            import polygonsToMasks
 

setupLogging ('log/learning/Idatafa2dbFrames.log', logging.INFO, 'a')


db_all_file   = 'databases/idatafa/166-Feb14-11h/init-allimages.db'
db_lab_file   = 'databases/idatafa/166-Feb14-11h/init-labelled.db'
# in_list_file = 'databases/idatafa/164-Feb14-11h/list.txt'
# (conn, cursor) = dbInit(db_all_file, db_lab_file)
# filterDbWithList (cursor, in_list_file)
# conn.commit()
# conn.close()


db_labparsed_file = 'databases/idatafa/166-Feb14-11h/parsed-labelled.db'
# annotations_dir = 'databases/idatafa/Annotations/166-Feb23-09h'
# params = { 'debug_show': True }
# (conn, cursor) = dbInit(db_lab_file, db_labparsed_file)
# folder2frames (cursor, annotations_dir, params)
# conn.commit()
# conn.close()

db_out_file = 'databases/idatafa/166-Feb14-11h/parsed.db'
(conn_lab, cursor_lab) = dbInit(db_labparsed_file)
(conn_all, cursor_all) = dbInit(db_all_file, db_out_file)
polygonsToMasks (cursor_all, cursor_lab, cursor_all)
conn_all.commit()
conn_all.close()
conn_lab.close()
