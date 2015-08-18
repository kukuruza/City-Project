import logging
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
from helperSetup import setupLogging
import sqlite3

setupLogging ('log/learning/UpgradeDb.log', logging.INFO, 'a')

db_in_path =  'datasets/sparse/Databases/119-Apr09-13h/src.db'


conn = sqlite3.connect (os.path.join(os.getenv('CITY_DATA_PATH'), db_in_path))
c = conn.cursor()

c.execute('CREATE TEMPORARY TABLE backup(imagefile,src,width,height,maskfile,time)')
c.execute('INSERT INTO backup SELECT ghostfile,src,width,height,maskfile,time FROM images')
c.execute('DROP TABLE images')
c.execute('CREATE TABLE images(imagefile,src,width,height,maskfile,time)')
c.execute('INSERT INTO images SELECT imagefile,src,width,height,maskfile,time FROM backup')
c.execute('DROP TABLE backup')

conn.commit()
conn.close()
