import logging
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
from helperSetup import setupLogging, dbInit
from dbFasterRcnn import _writeXmlString_, exportSparseCars
import helperH5
import h5py


setupLogging ('log/learning/exportFasterRcnn.log', logging.DEBUG, 'a')

in_db_path  = 'databases/sparse/119-Apr09-13h/angles-ghost.db'
out_dataset = '.'

(conn, cursor) = dbInit(os.path.join(os.getenv('CITY_DATA_PATH'), in_db_path))
#cursor.execute('SELECT imagefile FROM images')
#imagefile, = cursor.fetchone()
#cursor.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
#car_entries = cursor.fetchall()
#print len(car_entries)
#print _writeXmlString_ (cursor, imagefile, car_entries, {'dataset': 'test'})
exportSparseCars(cursor, 'tmp')
conn.close()
