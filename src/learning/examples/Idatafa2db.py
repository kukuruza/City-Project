import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
from learning.helperSetup         import setupLogging, dbInit
from learning.labelme.idatafa2db  import folder2frames
from learning.dbModify            import polygonsToMasks, polygonsToMasks_old
 

# annotations_dir = 'databases/idatafa/Annotations/166-Feb23-09h'
# params = { 'debug_show': True }
# (conn, cursor) = dbInit(db_lab_file, db_labparsed_file)
# folder2frames (cursor, annotations_dir, params)
# conn.commit()
# conn.close()

parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--out_db_file', required=True)
parser.add_argument('--logging_level', default=20, type=int)
args = parser.parse_args()

setupLogging ('log/learning/Idatafa2dbFrames.log', args.logging_level, 'a')

(conn, cursor) = dbInit(args.in_db_file, args.out_db_file)
polygonsToMasks_old (cursor)
conn.commit()
conn.close()



