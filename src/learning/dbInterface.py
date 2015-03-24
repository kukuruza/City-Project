import logging
import json
import sqlite3


def createLabelmeDb (db_path):
    conn = sqlite3.connect (db_path)
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS images
                     (imagefile TEXT PRIMARY KEY, 
                      src TEXT, 
                      width INTEGER, 
                      height INTEGER,
                      ghostfile TEXT,
                      maskfile TEXT
                      );''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS cars
                     (id INTEGER PRIMARY KEY,
                      imagefile INTEGER, 
                      name TEXT, 
                      x1 INTEGER,
                      y1 INTEGER,
                      width INTEGER, 
                      height INTEGER,
                      offsetx INTEGER,
                      offsety INTEGER,
                      yaw REAL,
                      pitch REAL,
                      color TEXT
                      );''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS polygons
                     (id INTEGER PRIMARY KEY,
                      carid TEXT, 
                      x INTEGER,
                      y INTEGER
                      );''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS matches
                     (id INTEGER PRIMARY KEY,
                      match INTEGER,
                      carid INTEGER
                      );''')
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
        cursor.execute('SELECT match FROM matches WHERE carid=?;', (carid,));
        match = cursor.fetchone()
        if match:
            cursor.execute('UPDATE matches SET carid=0 WHERE carid=?', (carid,))
            # if all cars are 0 for a match, delete it
            cursor.execute('SELECT carid FROM matches WHERE match=?;', (match[0],));
            carids = cursor.fetchall()
            if (all(carid[0] == 0 for carid in carids)):
                cursor.execute('DELETE FROM matches WHERE match=?;', (match[0],));





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



# not tested or used
def deleteEmptyImages():
    cursor.execute('SELECT imagefile FROM images');
    image_entries = cursor.fetchall()
    for (imagefile,) in image_entries:
        cursor.execute('SELECT count(id) FROM cars WHERE imagefile=(?)', (imagefile,));
        if cursor.fetchone()[0] > 0: continue
        cursor.execute('DELETE FROM images WHERE imagefile=?;', (imagefile,));
        os.remove( op.join(os.getenv('CITY_DATA_PATH'), imagefile) )
        #if checkTableExists (cursor, 'masks'):
        #    cursor.execute('SELECT FROM masks WHERE imagefile=?;', (imagefile,));
        #    os.remove( op.join(os.getenv('CITY_DATA_PATH'), imagefile) )



#
# check that db follows the rules
#
def checkTableExists (cursor, name):
    cursor.execute('''SELECT count(*) FROM sqlite_master 
                      WHERE name=? AND type='table';''', (name,))
    return cursor.fetchone()[0] != 0

def checkEntryExists (cursor, table, field, value):
    cursor.execute('SELECT count(*) FROM ? WHERE ? = ?', (table,field,value))
    if cursor.fetchone()[0] == 0:
        raise Exception ('table ' + table + ' does not have ' + field + '=' + value)


def checkDb (db_path):
    conn = sqlite3.connect (db_path)
    cursor = conn.cursor()

    checkTableExists (cursor, 'cars')
    checkTableExists (cursor, 'images')
    checkTableExists (cursor, 'matches')
    checkTableExists (cursor, 'polygons')

    cursor.execute('SELECT * FROM cars')
    cars = cursor.fetchall()
    for car in cars:
        # check image
        checkEntryExists (cursor, 'images','imagefile', queryField(car,'imagefile'))
        # check polygons
        carid = queryField(car, 'carid')
        cursor.execute('SELECT count(*) FROM polygons WHERE carid=?;', (carid,))
        if cursor.fetchone()[0] == 1 or cursor.fetchone()[0] == 2:
            raise Exception ('there are just 1 or 2 polygons for car ' + str(carid))

    
    conn.close()

    sys.exit()


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
    if field == 'offsetx':   return car[7]
    if field == 'offsety':   return car[8]
    if field == 'yaw':       return car[9]
    if field == 'pitch':     return car[10]

    if field == 'bbox':      
        return list(car[3:7])
    if field == 'bbox-w-offset': 
        return [car[3]+car[7], car[4]+car[8], car[5], car[6]]
    return None


def getImageField (image, field):
    if field == 'imagefile': return image[0] 
    if field == 'src':       return image[1] 
    if field == 'width':     return image[2] 
    if field == 'height':    return image[3] 
    return None


def getPolygonField (polygon, field):
    if field == 'id':        return polygon[0]
    if field == 'carid':     return polygon[1]
    if field == 'x':         return polygon[2]
    if field == 'y':         return polygon[3]
    return None




def parseFilterName (filter_name):
    # lack of dot means 'equal'
    numdots = filter_name.count('.')
    if numdots == 0: 
        filter_name = filter_name + '.equal'
    elif numdots > 1:
        raise Exception (str('filter "' + filter_name + '" has more than one dot'))
    (filter_key, filter_op) = filter_name.split('.')

    # substitute operation with SQL operation
    if filter_op == 'min':
        filter_op = '>='
    elif filter_op == 'max':
        filter_op = '<='
    elif filter_op == 'equal':
        filter_op = '='
    elif filter_op == 'not':
        filter_op = '<>'
    elif filter_op == 'in':
        filter_op = 'in'
    else:
        raise Exception ('operation of filter "' + filter_name + '" is unknown')

    return (filter_key, filter_op)



def queryCars (cursor, filters={}, fields=['*']):
    '''Finds objects in specified locations based on specified filters, 
       and returns an index of all suitable objects

       'filters' is a dictionary. E.g. 
          {'pitch.min' : -90, 'pitch.max' : -45, 'name' : 'car'} '''

    # fields
    fields_str = ','.join(fields)

    # constraints
    filters_str = ''
    if filters: filters_str = ' WHERE '
    # one-by-one
    for key, value in filters.iteritems():
        name, op = parseFilterName(key)
        if name in ['filter', 'resize']: continue
        filters_str += (name + ' ' + op + ' "' + str(value) + '" AND ')
    # remove the last AND
    if filters: filters_str = filters_str[:-5]

    # put them all together
    query_str = 'SELECT ' + fields_str + ' FROM cars' + filters_str

    # actual query
    logging.debug ('querying cars with: ' + query_str)
    cursor.execute(query_str)
    return cursor.fetchall()



