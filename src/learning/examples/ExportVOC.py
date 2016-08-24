import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
from learning.helperSetup import setupLogging, dbInit
from learning.dbExportVOC import _writeXmlString_, exportSparseCars


setupLogging ('log/learning/ExportFasterRcnn.log', logging.DEBUG, 'a')

in_db_file = 'databases/sparse/119-Apr09-13h/angles-ghost.db'
out_dataset = '.'

(conn, cursor) = dbInit(in_db_path)
#cursor.execute('SELECT imagefile FROM images')
#imagefile, = cursor.fetchone()
#cursor.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
#car_entries = cursor.fetchall()
#print len(car_entries)
#print _writeXmlString_ (cursor, imagefile, car_entries, {'dataset': 'test'})
exportSparseCars(cursor, 'tmp')
conn.close()
