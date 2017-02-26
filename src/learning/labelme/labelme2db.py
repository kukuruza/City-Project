import os, sys, os.path as op
import numpy as np
import cv2
#import xml.etree.ElementTree as ET
from lxml import etree as ET
import collections
import logging
import glob
import shutil
import sqlite3
from learning.helperDb import createTablePolygons
from learning.dbUtilities import *
from learning.helperSetup import setParamUnlessThere, atcity
from learning.labelme.parser import FrameParser, PairParser


    
def __pointsOfPolygon__ (annotation):
    pts = annotation.find('polygon').findall('pt')
    xs = []
    ys = []
    for pt in pts:
        xs.append( int(pt.find('x').text) )
        ys.append( int(pt.find('y').text) )
    return xs, ys


def __processFrame__ (c, imagefile, annotations_dir, params):

    # get paths and names
    imagename = op.basename(imagefile)
    annotation_name = op.splitext(imagename)[0] + '.xml'
    annotation_file = atcity(op.join(annotations_dir, annotation_name))
    logging.debug ('annotation_file: ' + annotation_file)

    # if annotation file does not exist then this imagre is not annotated
    if not op.exists(atcity(annotation_file)):
        logging.debug ('this image is not annotated. Skip it.')
        return

    tree = ET.parse(op.join(os.getenv('CITY_DATA_PATH'), annotation_file))

    # get dimensions
    c.execute('SELECT height,width FROM images WHERE imagefile=?', (imagefile,))
    sz = (height,width) = c.fetchone()

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
            logging.info ('degenerate polygon %s,%s in %s' % (str(xs), str(ys), annotation_name))
            continue

        # make roi
        roi = [min(ys), min(xs), max(ys), max(xs)]

        # validate roi
        if roi[0] < 0 or roi[1] < 0 or roi[2] >= sz[0] or roi[3] >= sz[1]:
            logging.warning ('roi %s out of borders: %s' % (str(roi), str(sz)))
        roi[0] = max(roi[0], 0)
        roi[1] = max(roi[1], 0)
        roi[2] = min(roi[2], sz[0]-1)
        roi[3] = min(roi[3], sz[1]-1)

        # make an entry for database
        bbox = roi2bbox (roi)
        car_entry = (imagefile, name, bbox[0], bbox[1], bbox[2], bbox[3])

        # write to db
        s = 'cars(imagefile,name,x1,y1,width,height)'
        c.execute('INSERT INTO %s VALUES (?,?,?,?,?,?);' % s, car_entry)

        carid = c.lastrowid
        for i in range(len(xs)):
            polygon = (carid, xs[i], ys[i])
            c.execute('INSERT INTO polygons(carid,x,y) VALUES (?,?,?);', polygon)

        if params['debug_show']: 
            #drawRoi (img, roi, (0,0), name, (255,255,255))
            pts = np.array([xs, ys], dtype=np.int32).transpose()
            cv2.polylines(img, [pts], True, (255,255,255))

    if params['debug_show']: 
        cv2.imshow('debug_show', img)
        cv2.waitKey(-1)




def folder2frames (c, annotations_dir, params):

    logging.info ('==== folder2frames ====')
    setParamUnlessThere (params, 'debug_show', False)
    params['parser'] = FrameParser()

    createTablePolygons(c)

    c.execute('SELECT imagefile FROM images')
    imagefiles = c.fetchall()

    for (imagefile,) in imagefiles:
        logging.debug ('processing imagefile: ' + imagefile)
        __processFrame__ (c, imagefile, annotations_dir, params)




# Parse labelme vstacked images into car-matches between frames
#
# Script takes a 'folder' name. 
# /Images/folder and /Annotations/folder are the results of the labelme,
#   Each image is two vertically stacked frames
#   Labelme annotations signify matches between frames
#


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



def __processPair__ (c, imagefile1, imagefile2, annotations_dir, params):

    # get annotations
    (labelme_dir, folder) = somefile2dirs (imagefile1)
    imagename1strip = op.splitext(op.basename(imagefile1))[0]
    imagename2strip = op.splitext(op.basename(imagefile2))[0]
    annotation_name = imagename1strip + '-' + imagename2strip + '.xml'
    annotation_file = atcity(op.join(annotations_dir, annotation_name))
    tree = ET.parse(op.join(os.getenv('CITY_DATA_PATH'), annotation_file))

    objects = tree.getroot().findall('object')
    captions_t = []
    captions_b = []
    cars_t = []
    cars_b = []

    c.execute('SELECT width,height FROM images WHERE imagefile = ?', (imagefile1,))
    (width,height) = c.fetchone()

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
            drawRoi (imgpair, roi, name, (255,255,255))
            #pts = np.array([xs, ys], dtype=np.int32).transpose()
            #cv2.polylines(imgpair, [pts], True, (255,255,255))

        # get roi
        is_top = np.mean(np.mean(ys)) < height
        if not is_top: 
            ys = [y-height for y in ys]
        roi = [min(ys), min(xs), max(ys), max(xs)]
        
        # validate roi
        if roi[0] < 0 or roi[1] < 0 or roi[2] >= height or roi[3] >= width:
            logging.warning ('roi ' + str(roi) + ' out of borders: ' + str((width,height)));
        roi[0] = max(roi[0], 0)
        roi[1] = max(roi[1], 0)
        roi[2] = min(roi[2], height-1)
        roi[3] = min(roi[3], width-1)

        # make an entry for database
        bbox = roi2bbox (roi)
        car_entry = (imagefile1 if is_top else imagefile2,
                     name, bbox[0], bbox[1], bbox[2], bbox[3])

        # write car to db
        s = 'cars(imagefile,name,x1,y1,width,height)'
        c.execute('INSERT INTO ' + s + ' VALUES (?,?,?,?,?,?);', car_entry)
        carid = c.lastrowid
        for i in range(len(xs)):
            polygon = (carid,xs[i],ys[i])
            c.execute('INSERT INTO polygons(carid,x,y) VALUES (?,?,?);', polygon)

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
        c.execute('SELECT MAX(match) FROM matches')
        match = c.fetchone()[0]
        match = 0 if match is None else match + 1
        # insert a match entry for every car. Matched car will have the same match.
        if pair[0]:
            c.execute('INSERT INTO matches(match,carid) VALUES (?,?);', (match,pair[0]))
        if pair[1]:
            c.execute('INSERT INTO matches(match,carid) VALUES (?,?);', (match,pair[1]))
        if pair[0] and pair[1] and params['debug_show']:
            c.execute('SELECT x1,y1,width,height FROM cars WHERE id = ?', (pair[0],))
            bbox1 = c.fetchone()
            c.execute('SELECT x1,y1,width,height FROM cars WHERE id = ?', (pair[1],))
            bbox2 = c.fetchone()
            bbox2 = (bbox2[0], bbox2[1]+height, bbox2[2], bbox2[3])
            center1 = getCenter(bbox2roi(bbox1))
            center2 = getCenter(bbox2roi(bbox2))
            cv2.line (imgpair, center1, center2, (255,0,0))

    if not pairs: logging.warning ('file has no valid polygons: ' + annotation_file)

    if params['debug_show']: 
        cv2.imshow('debug_show', imgpair)
        cv2.waitKey(-1)



def __mergeSameCars__ (c, imagefile, params):

    c.execute('SELECT height,width FROM images WHERE imagefile=?', (imagefile,))
    (height,width) = c.fetchone()
    params['imgshape'] = (height,width)

    c.execute('SELECT id FROM cars WHERE imagefile=?', (imagefile,))
    carids = c.fetchall()
    logging.debug (str(len(carids)) + ' objects found for ' + op.basename(imagefile))

    # collect polygons from all cars
    polygons = []
    for (carid,) in carids:
        c.execute('SELECT x,y FROM polygons WHERE carid=?', (carid,))
        polygons.append(c.fetchall())

    # cluster rois
    rois_clustered, assignments = hierarchicalClusterPolygons (polygons, params)
    clusters = []
    for assignment in list(set(assignments)):
        cluster = [x for i, (x,) in enumerate(carids) if assignments[i] == assignment]
        clusters.append(cluster)

    if params['debug_show']: 
        img = cv2.imread(op.join(os.getenv('CITY_DATA_PATH'), imagefile))
        for polygon in polygons:
            roi = polygon2roi(polygon)
            drawRoi (img, roi, None, (0,0,255))
        for roi in rois_clustered:
            drawRoi (img, roi, None, (0,255,0))
        cv2.imshow('debug_show', img)
        cv2.waitKey(-1)

    # update db
    for i in range(len(clusters)):

        roi0 = rois_clustered[i]
        if roi0[0] < 0 or roi0[1] < 0 or roi0[2] >= height or roi0[3] >= width:
            logging.warning ('roi ' + str(roi0) + ' out of borders: ' + str((width,height)));
        roi0[0] = max(roi0[0], 0)
        roi0[1] = max(roi0[1], 0)
        roi0[2] = min(roi0[2], height-1)
        roi0[3] = min(roi0[3], width-1)

        # most will be just single elements
        cluster = clusters[i]
        if not isinstance (cluster, list):
            continue            

        carid0 = cluster[0]

        # change 1st car bbox to the cluster center
        bbox0 = roi2bbox(roi0)
        entry = (bbox0[0], bbox0[1], bbox0[2], bbox0[3], carid0)
        c.execute('UPDATE cars SET x1=?, y1=?, width=?, height=? WHERE id=?', entry)

        # check the names
        names = []
        for carid in cluster:
            c.execute('SELECT name FROM cars WHERE id = ?', (carid,))
            (name,) = c.fetchone()
            names.append(name)
        if len(set(names)) > 1:
            logging.warning ('carid: ' + str(carid0) + ' has several names: ' + str(names))

        # get the match of the 1st car
        c.execute('SELECT match FROM matches WHERE carid = ?', (carid0,))
        match0 = c.fetchone()
        if match0 is None: continue;   # it was a duplicate car (error in labelling)

        # all other cars in cluster -- update all that match with them and then delete them
        for j in range(1, len(cluster)):
            carid = cluster[j]
            c.execute('DELETE FROM cars WHERE id = ?', (carid,));
            c.execute('SELECT match FROM matches WHERE carid = ?', (carid,))
            match = c.fetchone()
            if match is None: continue;   # it was a duplicate car (error in labelling)
            c.execute('UPDATE matches SET match = ? WHERE match = ?', (match0[0], match[0]))
            c.execute('DELETE FROM matches WHERE carid = ?', (carid,));

        c.execute('SELECT carid FROM matches WHERE match = ?', match0)
        newids = c.fetchall()
        logging.debug ('match: ' + str(match0[0]) + ' has cars: ' + str(newids))



def folder2pairs (c, annotations_dir, params):

    logging.info ('==== folder2pairs ====')
    setParamUnlessThere (params, 'debug_show', False)
    setParamUnlessThere (params, 'threshold', 0.6)
    params['parser'] = PairParser()

    createTablePolygons (c)

    c.execute('SELECT imagefile FROM images')
    imagefiles = c.fetchall()

    # match top and bottom of every image
    for i in range(len(imagefiles)-1):
        (imagefile1,) = imagefiles[i]
        (imagefile2,) = imagefiles[i+1]
        logging.debug ('processing imagepair: ' + imagefile1 + ' - ' + imagefile2)
        __processPair__ (c, imagefile1, imagefile2, annotations_dir, params)

    # merge bottom-image1 to top-image2
    for (imagefile,) in imagefiles:
        logging.debug ('merging cars in imagefile: ' + imagefile)
        __mergeSameCars__ (c, imagefile, params)

    c.execute('DROP TABLE polygons')

