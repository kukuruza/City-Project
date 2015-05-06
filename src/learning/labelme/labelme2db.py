import numpy as np
import cv2
import xml.etree.ElementTree as ET
import os, sys
import collections
import logging
import os.path as op
import glob
import shutil
import sqlite3
sys.path.insert(0, os.path.abspath('..'))
from dbInterface import createLabelmeDb, deleteAll4imagefile, getImageField, queryField
import utilities
from utilities import roi2bbox, image2ghost, getCenter, bbox2roi
import setupHelper
import processing

sys.path.insert(0, os.path.abspath('annotations'))
from annotations.parser import FrameParser, PairParser


    
def __pointsOfPolygon__ (annotation):
    pts = annotation.find('polygon').findall('pt')
    xs = []
    ys = []
    for pt in pts:
        xs.append( int(pt.find('x').text) )
        ys.append( int(pt.find('y').text) )
    return xs, ys


def __createPolygonsTable__ (cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS polygons
                     (id INTEGER PRIMARY KEY,
                      carid TEXT, 
                      x INTEGER,
                      y INTEGER
                      );''')


def __processFrame__ (cursor, imagefile, params):

    # get paths and names
    (labelme_dir, folder) = utilities.somefile2dirs (imagefile)
    imagename = op.basename(imagefile)
    annotation_name = op.splitext(imagename)[0] + '.xml'
    annotation_file = op.join(labelme_dir, 'Annotations', folder, annotation_name)
    logging.debug ('annotation_file: ' + annotation_file)

    tree = ET.parse(op.join(os.getenv('CITY_DATA_PATH'), annotation_file))

    # consistancy between folder and image in anntation and imagefile
    folder_ann = tree.getroot().find('folder').text
    imagename_ann = tree.getroot().find('filename').text
    if (folder_ann != folder):
        logging.warning('folder: ' + folder + ', folder_ann: ' + folder_ann)
    if (imagename_ann != imagename):
        logging.warning('imagename: ' + imagename + ', imagename_ann: ' + imagename_ann)

    if params['debug_show']:
        img = cv2.imread(op.join(os.getenv('CITY_DATA_PATH'), imagefile))

    for object_ in tree.getroot().findall('object'):

        # skip if it was deleted
        if object_.find('deleted').text == '1': continue

        # find the name of object. Filter all generic objects
        name = params['parser'].parse(object_.find('name').text)
        if name == 'object':
            logging.info('skipped an "object"')
            continue
        if name is None:
            logging.info('skipped a None')
            continue

        # get all the points
        xs, ys = __pointsOfPolygon__(object_)

        # replace pointers to small squares
        if len(xs) == 1:
            d = 5
            xs = [xs[0]-d, xs[0]-d, xs[0]+d, xs[0]+d]
            ys = [ys[0]+d, ys[0]-d, ys[0]-d, ys[0]+d]

        # filter out degenerate polygons
        if len(xs) == 2 or min(xs) == max(xs) or min(ys) == max(ys):
            logging.info ('degenerate polygon ' + str(xs) + ',' + str(ys) + 'in: ' + annotation_name)
            continue

        # make bbox
        roi = [min(ys), min(xs), max(ys), max(xs)]

        # make an entry for database
        bbox = roi2bbox (roi)
        car_entry = (imagefile, name, bbox[0], bbox[1], bbox[2], bbox[3])

        # write to db
        s = 'cars(imagefile,name,x1,y1,width,height)'
        cursor.execute('INSERT INTO ' + s + ' VALUES (?,?,?,?,?,?);', car_entry)

        carid = cursor.lastrowid
        for i in range(len(xs)):
            polygon = (carid, xs[i], ys[i])
            cursor.execute('INSERT INTO polygons(carid,x,y) VALUES (?,?,?);', polygon)

        if params['debug_show']: 
            #utilities.drawRoi (img, roi, (0,0), name, (255,255,255))
            pts = np.array([xs, ys], dtype=np.int32).transpose()
            cv2.polylines(img, [pts], True, (255,255,255))

    if params['debug_show']: 
        cv2.imshow('debug_show', img)
        cv2.waitKey(-1)




def folder2frames (db_in_path, db_out_path, params):

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    db_in_path   = op.join(CITY_DATA_PATH, db_in_path)
    db_out_path  = op.join(CITY_DATA_PATH, db_out_path)

    setupHelper.setupLogHeader (db_in_path, db_out_path, params, 'folder2frames')
    setupHelper.setupCopyDb (db_in_path, db_out_path)

    params = setupHelper.setParamUnlessThere (params, 'debug_show', False)
    params['parser'] = FrameParser()

    conn = sqlite3.connect (db_out_path)
    cursor = conn.cursor()

    __createPolygonsTable__(cursor)

    cursor.execute('SELECT imagefile FROM images')
    imagefiles = cursor.fetchall()

    for (imagefile,) in imagefiles:
        logging.debug ('processing imagefile: ' + imagefile)
        __processFrame__ (cursor, imagefile, params)

    conn.commit()
    conn.close()




# Parse labelme vstacked images into car-matches between frames
#
# Script takes a 'folder' name. 
# /Images/folder and /Annotations/folder are the results of the labelme,
#   Each image is two vertically stacked frames
#   Labelme annotations signify matches between frames
#


def __createMatchesTable__ (cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS matches
                     (id INTEGER PRIMARY KEY,
                      match INTEGER,
                      carid INTEGER
                      );''')


def __bypartiteMatch__ (captions_t, captions_b, cars_t, cars_b, file_name):
    pairs = []

    # for every element in top list find its match in the bottom list
    for caption in captions_t:

        indices_t = [x for x, y in enumerate(captions_t) if y == caption]
        if len(indices_t) > 1:
            logging.error ('duplicates "' + str(caption) + '" on top in: ' + file_name)
            continue

        indices_b = [x for x, y in enumerate(captions_b) if y == caption]
        if len(indices_b) > 1:
            logging.error ('duplicates "' + str(caption) + '" on bottom in: ' + file_name)
            continue

        assert (len(indices_t) <= 1 and len(indices_b) <= 1)
        if indices_t and indices_b:
            logging.debug ('a valid pair "' + str(caption) + '" in: ' + file_name)
            car_pair = (cars_t[indices_t[0]], cars_b[indices_b[0]])
            captions_b[indices_b[0]] = None
        elif indices_t and not indices_b:
            logging.debug ('a valid top "' + str(caption) + '" in: ' + file_name)
            car_pair = (cars_t[indices_t[0]], None)

        pairs.append(car_pair)

    # collect the rest from the bottom list
    for caption in captions_b:
        if caption is None: continue

        indices_b = [x for x, y in enumerate(captions_b) if y == caption]
        if len(indices_b) > 1:
            logging.error ('duplicates "' + str(caption) + '" on bottom in: ' + file_name)
            continue

        if caption:
            logging.debug ('a valid bottom "' + str(caption) + '" in: ' + file_name)
            car_pair = (None, cars_b[indices_b[0]])
            pairs.append(car_pair)

    return pairs



def __processPair__ (cursor, imagefile1, imagefile2, params):

    # get annotations
    (labelme_dir, folder) = utilities.somefile2dirs (imagefile1)
    imagename1strip = op.splitext(op.basename(imagefile1))[0]
    imagename2strip = op.splitext(op.basename(imagefile2))[0]
    annotation_name = imagename1strip + '-' + imagename2strip + '.xml'
    annotation_file = op.join(labelme_dir, 'Annotations', folder, annotation_name)
    tree = ET.parse(op.join(os.getenv('CITY_DATA_PATH'), annotation_file))

    objects = tree.getroot().findall('object')
    captions_t = []
    captions_b = []
    cars_t = []
    cars_b = []

    cursor.execute('SELECT height FROM images WHERE imagefile = ?', (imagefile1,))
    (height,) = cursor.fetchone()

    if params['debug_show']:
        amazonpair_name = imagename1strip + '-' + imagename2strip + '.jpg'
        amazonpair_file = op.join(labelme_dir, 'Pairs', folder, amazonpair_name)
        pair_path = op.join(os.getenv('CITY_DATA_PATH'), amazonpair_file)
        if not op.exists(pair_path): 
            raise Exception('pair_path does not exist: ' + pair_path) 
        imgpair = cv2.imread(pair_path)

    # collect captions and assign statuses accordingly
    for object_ in objects:

        # skip if it was deleted
        if object_.find('deleted').text == '1': continue

        # get all the points
        xs, ys = __pointsOfPolygon__ (object_)

        # replace pointers to small squares
        if len(xs) == 1:
            d = 5
            xs = [xs[0]-d, xs[0]-d, xs[0]+d, xs[0]+d]
            ys = [ys[0]+d, ys[0]-d, ys[0]-d, ys[0]+d]

        # filter out degenerate polygons
        if len(xs) == 2 or min(xs) == max(xs) or min(ys) == max(ys):
            logging.info ('degenerate polygon ' + str(xs) + ',' + str(ys) + 'in: ' + annotation_name)
            continue

        # find the name of object. Filter all generic objects
        (name, number) = params['parser'].parse(object_.find('name').text)
        if name is None or number is None:
            logging.info('skipped a None')
            continue

        if params['debug_show']: 
            roi = [min(ys), min(xs), max(ys), max(xs)]
            utilities.drawRoi (imgpair, roi, (0,0), name, (255,255,255))
            #pts = np.array([xs, ys], dtype=np.int32).transpose()
            #cv2.polylines(imgpair, [pts], True, (255,255,255))

        # get bbox
        is_top = np.mean(np.mean(ys)) < height
        if not is_top: 
            ys = [y-height for y in ys]
        roi = [min(ys), min(xs), max(ys), max(xs)]

        # make an entry for database
        bbox = roi2bbox (roi)
        car_entry = (imagefile1 if is_top else imagefile2,
                     name, bbox[0], bbox[1], bbox[2], bbox[3])

        # write car to db
        s = 'cars(imagefile,name,x1,y1,width,height)'
        cursor.execute('INSERT INTO ' + s + ' VALUES (?,?,?,?,?,?);', car_entry)
        carid = cursor.lastrowid
        for i in range(len(xs)):
            polygon = (carid,xs[i],ys[i])
            cursor.execute('INSERT INTO polygons(carid,x,y) VALUES (?,?,?);', polygon)
    
        # write to either top or bottom stack
        if is_top:
            captions_t.append((name, number))
            cars_t.append (carid)
        else:
            captions_b.append((name, number))
            cars_b.append (carid)

    pairs = __bypartiteMatch__ (captions_t, captions_b, cars_t, cars_b, annotation_name)

    # write matches to db
    for pair in pairs:
        # take the largest 'match' number
        cursor.execute('SELECT MAX(match) FROM matches')
        match = cursor.fetchone()[0]
        match = 0 if match is None else match + 1
        # insert a match entry for every car. Matched car will have the same match.
        if pair[0]:
            cursor.execute('INSERT INTO matches(match,carid) VALUES (?,?);', (match,pair[0]))
        if pair[1]:
            cursor.execute('INSERT INTO matches(match,carid) VALUES (?,?);', (match,pair[1]))
        if pair[0] and pair[1] and params['debug_show']:
            cursor.execute('SELECT x1,y1,width,height FROM cars WHERE id = ?', (pair[0],))
            bbox1 = cursor.fetchone()
            cursor.execute('SELECT x1,y1,width,height FROM cars WHERE id = ?', (pair[1],))
            bbox2 = cursor.fetchone()
            bbox2 = (bbox2[0], bbox2[1]+height, bbox2[2], bbox2[3])
            center1 = tuple(reversed(list(getCenter(bbox2roi(bbox1)))))
            center2 = tuple(reversed(list(getCenter(bbox2roi(bbox2)))))
            cv2.line (imgpair, center1, center2, (255,0,0))

    if not pairs: logging.warning ('file has no valid polygons: ' + annotation_file)

    if params['debug_show']: 
        cv2.imshow('debug_show', imgpair)
        cv2.waitKey(-1)



def __mergeSameCars__ (cursor, imagefile, params):

    cursor.execute('SELECT height,width FROM images WHERE imagefile=?', (imagefile,))
    params['imgshape'] = cursor.fetchone()

    cursor.execute('SELECT id FROM cars WHERE imagefile=?', (imagefile,))
    carids = cursor.fetchall()
    logging.debug (str(len(carids)) + ' objects found for ' + op.basename(imagefile))

    # collect polygons from all cars
    polygons = []
    for (carid,) in carids:
        cursor.execute('SELECT x,y FROM polygons WHERE carid=?', (carid,))
        polygons.append(cursor.fetchall())

    # cluster rois
    rois_clustered, assignments = utilities.hierarchicalClusterPolygons (polygons, params)
    clusters = []
    for assignment in list(set(assignments)):
        cluster = [x for i, (x,) in enumerate(carids) if assignments[i] == assignment]
        clusters.append(cluster)

    if params['debug_show']: 
        img = cv2.imread(op.join(os.getenv('CITY_DATA_PATH'), imagefile))
        for polygon in polygons:
            roi = utilities.polygon2roi(polygon)
            utilities.drawRoi (img, roi, (0,0), None, (0,0,255))
        for roi in rois_clustered:
            utilities.drawRoi (img, roi, (0,0), None, (0,255,0))
        cv2.imshow('debug_show', img)
        cv2.waitKey(-1)

    # update db
    for i in range(len(clusters)):
        roi0 = rois_clustered[i]
        cluster = clusters[i]

        # most will be just single elements
        if not isinstance (cluster, list):
            continue            

        carid0 = cluster[0]

        # change 1st car bbox to the cluster center
        bbox0 = roi2bbox(roi0)
        entry = (bbox0[0], bbox0[1], bbox0[2], bbox0[3], carid0)
        cursor.execute('UPDATE cars SET x1=?, y1=?, width=?, height=? WHERE id=?', entry)

        # check the names
        names = []
        for carid in cluster:
            cursor.execute('SELECT name FROM cars WHERE id = ?', (carid,))
            (name,) = cursor.fetchone()
            names.append(name)
        if len(set(names)) > 1:
            logging.warning ('carid: ' + str(carid0) + ' has several names: ' + str(names))

        # get the match of the 1st car
        cursor.execute('SELECT match FROM matches WHERE carid = ?', (carid0,))
        match0 = cursor.fetchone()
        if match0 is None: continue;   # it was a duplicate car (error in labelling)

        # all other cars in cluster -- update all that match with them and then delete them
        for j in range(1, len(cluster)):
            carid = cluster[j]
            cursor.execute('DELETE FROM cars WHERE id = ?', (carid,));
            cursor.execute('SELECT match FROM matches WHERE carid = ?', (carid,))
            match = cursor.fetchone()
            if match is None: continue;   # it was a duplicate car (error in labelling)
            cursor.execute('UPDATE matches SET match = ? WHERE match = ?', (match0[0], match[0]))
            cursor.execute('DELETE FROM matches WHERE carid = ?', (carid,));

        cursor.execute('SELECT carid FROM matches WHERE match = ?', match0)
        newids = cursor.fetchall()
        logging.debug ('match: ' + str(match0[0]) + ' has cars: ' + str(newids))



def folder2pairs (db_in_path, db_out_path, params):

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    db_in_path   = op.join(CITY_DATA_PATH, db_in_path)
    db_out_path  = op.join(CITY_DATA_PATH, db_out_path)

    setupHelper.setupLogHeader (db_in_path, db_out_path, params, 'folder2pairs')
    setupHelper.setupCopyDb (db_in_path, db_out_path)

    params = setupHelper.setParamUnlessThere (params, 'debug_show', False)
    params = setupHelper.setParamUnlessThere (params, 'threshold', 0.6)
    params['parser'] = PairParser()

    conn = sqlite3.connect (db_out_path)
    cursor = conn.cursor()

    __createPolygonsTable__(cursor)
    __createMatchesTable__(cursor)

    cursor.execute('SELECT imagefile FROM images')
    imagefiles = cursor.fetchall()

    # match top and bottom of every image
    for i in range(len(imagefiles)-1):
        (imagefile1,) = imagefiles[i]
        (imagefile2,) = imagefiles[i+1]
        logging.debug ('processing imagepair: ' + imagefile1 + ' - ' + imagefile2)
        __processPair__ (cursor, imagefile1, imagefile2, params)

    # merge bottom-image1 to top-image2
    for (imagefile,) in imagefiles:
        logging.debug ('merging cars in imagefile: ' + imagefile)
        __mergeSameCars__ (cursor, imagefile, params)

    cursor.execute('DROP TABLE polygons')

    conn.commit()
    conn.close()

