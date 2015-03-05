import logging
import os, sys
import os.path as OP
import shutil
import glob
import json
import numpy as np, cv2
import sqlite3


#
# all knowledge about 'cars' table is here
#
def queryField (car_entry, field):
    if field == 'id':        return car_entry[0]
    if field == 'imagefile': return car_entry[1] 
    if field == 'name':      return car_entry[2] 
    if field == 'x1':        return car_entry[3]
    if field == 'y1':        return car_entry[4]
    if field == 'width':     return car_entry[5]
    if field == 'height':    return car_entry[6]
    if field == 'offsetx':   return car_entry[7]
    if field == 'offsety':   return car_entry[8]
    if field == 'yaw':       return car_entry[9]
    if field == 'pitch':     return car_entry[10]
    return None



def image2ghost (image, backimage):
    assert (image is not None)
    assert (backimage is not None)
    return np.uint8((np.int32(image) - np.int32(backimage)) / 2 + 128)



def getGhost (labelme_dir, car_entry, backimage):
    assert (car_entry is not None)
    #print (car_entry)

    carid = queryField (car_entry, 'id')
    imagefile = queryField (car_entry, 'imagefile')
    width = queryField (car_entry, 'width')
    height = queryField (car_entry, 'height')
    offsetx = queryField (car_entry, 'offsetx')
    offsety = queryField (car_entry, 'offsety')
    x1 = offsetx + queryField (car_entry, 'x1')
    y1 = offsety + queryField (car_entry, 'y1')

    imagepath = OP.join (labelme_dir, 'Images', imagefile)
    if not OP.exists (imagepath):
        raise Exception ('imagepath does not exist: ' + imagepath)
    image = cv2.imread(imagepath)
    ghostimage = image2ghost (image, backimage)

    ghost = ghostimage [y1:y1+height, x1:x1+width]
    return (carid, imagefile, ghost)



def parseFilterName (filter_name):
    # lack of dot means 'equal'
    numdots = filter_name.count('.')
    if numdots == 0: 
        filter_name = filter_name + '.equal'
    elif numdots > 1:
        raise Exception (str('filter "' + filter_name + '" has more than one dot'))
    filter_parts = filter_name.split('.')
    assert len(filter_parts) == 2

    # check operations
    filter_key = filter_parts[0]
    filter_op = filter_parts[1]
    if filter_op not in ['min', 'max', 'equal']:
        raise Exception ('operation of filter "' + filter_name + '" is unknown')

    # substitute operation with SQL operation
    if filter_op == 'min':
        filter_op = '>='
    elif filter_op == 'max':
        filter_op = '<='
    elif filter_op == 'equal':
        filter_op = '='

    return (filter_key, filter_op)



def directQuery (db_path, query_str):
    # send the query and return the response
    conn = sqlite3.connect (db_path)
    cursor = conn.cursor()
    cursor.execute(query_str)
    response = cursor.fetchall()
    conn.close()
    return response



def queryCars (db_path, filters={}, fields=['*']):
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
    return directQuery (db_path, query_str)

