import logging
import json
import sqlite3


def checkTableExists (cursor, name):
    cursor.execute('''SELECT count(*) FROM sqlite_master 
                      WHERE name=? AND type='table';''', (name,))
    return cursor.fetchone()[0] != 0


def checkEntryExists (cursor, table, field, value):
    cursor.execute('SELECT count(*) FROM ? WHERE ? = ?', (table,field,value))
    if cursor.fetchone()[0] == 0:
        raise Exception ('table %s does not have %s = %s' % (table,field,str(value)))


def createTableImages (cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS images
                     (imagefile TEXT PRIMARY KEY, 
                      src TEXT, 
                      width INTEGER, 
                      height INTEGER,
                      ghostfile TEXT,
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


def createDbFromConn (conn):
    cursor = conn.cursor()

    #createTableSets(cursor)
    createTableImages(cursor)
    createTableCars(cursor)
    createTableMatches(cursor)


# remove this
def createDb (db_path):
    conn = sqlite3.connect (db_path)
    createDbFromConn (conn)
    conn.commit()
    conn.close()



def createLabelmeDb (db_path):
    conn = sqlite3.connect (db_path)
    cursor = conn.cursor()

    createTableImages(cursor)
    createTableCars(cursor)
    createTablePolygons(cursor)
    createTableMatches(cursor)
    conn.commit()
    conn.close()





#
# delete one car keeping db consistancy
#
def deleteCar (cursor, carid):
    cursor.execute('DELETE FROM cars WHERE id=?;', (carid,));
    if checkTableExists (cursor, 'polygons'):
        cursor.execute('DELETE FROM polygons WHERE carid=?;', (carid,));
    if checkTableExists (cursor, 'matches'):
        cursor.execute('DELETE FROM matches  WHERE carid=?;', (carid,));




#
# delete everything associated with an imagefile from the db
#
def deleteAll4imagefile (cursor, imagefile):
    #
    # find and delete image file
    cursor.execute('DELETE FROM images WHERE imagefile=(?)', (imagefile,));
    #
    # find and delete cars
    cursor.execute('SELECT id FROM cars WHERE imagefile=(?);', (imagefile,));
    carids = cursor.fetchall()
    carids = [str(carid[0]) for carid in carids]
    carids_str = '(' + ','.join(carids) + ')'
    cursor.execute('DELETE FROM cars     WHERE id IN ' + carids_str);
    #
    # delete polygons for cars
    cursor.execute('DELETE FROM polygons WHERE carid IN ' + carids_str);
    #
    # find and delete the matches
    cursor.execute('SELECT match FROM matches WHERE carid IN ' + carids_str);
    matches = cursor.fetchall()
    matches = [str(match[0]) for match in matches]
    matches_str = '(' + ','.join(matches) + ')'
    cursor.execute('DELETE FROM matches  WHERE match IN ' + matches_str);
    #
    logging.debug ('delete cars, polygons, matches from table: ' + ','.join(carids))


#
# all knowledge about 'cars' table is here
#
def queryField (car, field):
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


def getImageField (image, field):
    if field == 'imagefile': return image[0] 
    if field == 'src':       return image[1] 
    if field == 'width':     return image[2] 
    if field == 'height':    return image[3] 
    if field == 'ghostfile': return image[4] 
    if field == 'maskfile':  return image[5] 
    if field == 'time':      return image[6] 
    return None


def getPolygonField (polygon, field):
    if field == 'id':        return polygon[0]
    if field == 'carid':     return polygon[1]
    if field == 'x':         return polygon[2]
    if field == 'y':         return polygon[3]
    return None
