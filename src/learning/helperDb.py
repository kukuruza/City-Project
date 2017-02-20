import logging
import json
import sqlite3
from datetime import datetime


def doesTableExist (cursor, table):
    cursor.execute('''SELECT count(*) FROM sqlite_master 
                      WHERE name=? AND type='table';''', (table,))
    return cursor.fetchone()[0] != 0


def isColumnInTable (cursor, table, column):
    if not doesTableExist(cursor, table):
        raise Exception ('table %s does not exist' % table)
    cursor.execute('PRAGMA table_info(%s)' % table)
    return column in [x[1] for x in cursor.fetchall()]


def createTableImages (cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS images
                     (imagefile TEXT PRIMARY KEY, 
                      src TEXT, 
                      width INTEGER, 
                      height INTEGER,
                      maskfile TEXT,
                      time TIMESTAMP
                      );''')


def createTableCars (cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS cars
                     (id INTEGER PRIMARY KEY,
                      imagefile TEXT, 
                      name TEXT, 
                      x1 INTEGER,
                      y1 INTEGER,
                      width INTEGER, 
                      height INTEGER,
                      score REAL,
                      yaw REAL,
                      pitch REAL,
                      color TEXT
                      );''')


def createTablePolygons (cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS polygons
                     (id INTEGER PRIMARY KEY,
                      carid INTEGER, 
                      x INTEGER,
                      y INTEGER
                      );''')


def createTableMatches (cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS matches
                     (id INTEGER PRIMARY KEY,
                      match INTEGER,
                      carid INTEGER
                     );''')


# TODO: change conn to cursor
def createDb (conn):
    cursor = conn.cursor()

    conn.execute('PRAGMA user_version = 3')
    #createTableSets(cursor)
    createTableImages(cursor)
    createTableCars(cursor)
    createTableMatches(cursor)


def deleteCar (cursor, carid):
    ''' delete all information about a single car '''
    cursor.execute('DELETE FROM cars WHERE id=?;', (carid,));
    cursor.execute('DELETE FROM matches  WHERE carid=?;', (carid,));
    if doesTableExist (cursor, 'polygons'):
        cursor.execute('DELETE FROM polygons WHERE carid=?;', (carid,));


def carField (car, field):
    ''' all knowledge about 'cars' table is here '''
    if field == 'id':        return car[0]
    if field == 'imagefile': return car[1] 
    if field == 'name':      return car[2] 
    if field == 'x1':        return car[3]
    if field == 'y1':        return car[4]
    if field == 'width':     return car[5]
    if field == 'height':    return car[6]
    if field == 'score':     return car[7]
    if field == 'yaw':       return car[8]
    if field == 'pitch':     return car[9]
    if field == 'color':     return car[10]

    if field == 'bbox':      
        return list(car[3:7])
    if field == 'roi':
        bbox = list(car[3:7])
        return [bbox[1], bbox[0], bbox[3]+bbox[1]-1, bbox[2]+bbox[0]-1]
    return None


def imageField (image, field):
    if field == 'imagefile': return image[0] 
    if field == 'src':       return image[1] 
    if field == 'width':     return image[2] 
    if field == 'height':    return image[3] 
    if field == 'maskfile':  return image[4] 
    if field == 'time':      return image[5] 
    return None


def polygonField (polygon, field):
    if field == 'id':        return polygon[0]
    if field == 'carid':     return polygon[1]
    if field == 'x':         return polygon[2]
    if field == 'y':         return polygon[3]
    return None


def makeTimeString (time):
    ''' Write a string in my format.
    Args: time -- datetime object
    '''
    return datetime.strftime(time, '%Y-%m-%d %H:%M:%S.%f')


def parseTimeString (timestring):
    return datetime.strptime(timestring, '%Y-%m-%d %H:%M:%S.%f')


