#!/bin/python

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
from dbInterface import createDb, deleteAll4imagefile

sys.path.insert(0, os.path.abspath('annotations'))
from annotations.parser import FrameParser, PairParser


#
# roi - all inclusive, like in Matlab
# crop = im[roi[0]:roi[2]+1, roi[1]:roi[3]+1] (differs from Matlab)
#
def roi2bbox (roi):
    assert (isinstance(roi, list) and len(roi) == 4)
    return [roi[1], roi[0], roi[3]-roi[1]+1, roi[2]-roi[0]+1]



class BaseConverter:

    labelme_dir = ''
    debug_show = False

    def __init__(self, db_path, params):

        if 'debug_show' in params.keys():
            self.debug_show = params['debug_show']
        if 'labelme_dir' in params.keys():
            self.labelme_dir = params['labelme_dir']

        createDb (db_path)
        self.conn = sqlite3.connect (db_path)
        self.cursor = self.conn.cursor()


    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.conn.close()




    def imagefileOfAnnotation (self, annotation):
        folder = annotation.find('folder').text
        imagename = annotation.find('filename').text
        imagepath = op.join (os.getenv('CITY_DATA_PATH'), self.labelme_dir, 
                             'labelme/Images', folder, imagename)
        if not op.exists (imagepath):
            raise Exception ('no image at path ' + imagepath)
        return op.join (folder, imagename)

    
    def pointsOfPolygon (self, annotation):
        pts = annotation.find('polygon').findall('pt')
        xs = []
        ys = []
        for pt in pts:
            xs.append( int(pt.find('x').text) )
            ys.append( int(pt.find('y').text) )
        return xs, ys


    def debugShowAddRoi (self, img, roi, color):
        if self.debug_show: 
            cv2.rectangle (img, (roi[1], roi[0]), (roi[3], roi[2]), color)




class FrameConverter (BaseConverter):

    def __init__(self, db_path, params):
        BaseConverter.__init__(self, db_path, params)
        self.parser = FrameParser()


    def processImage (self, folder, annotation_file):
        logging.debug ('working with ' + annotation_file)

        tree = ET.parse(op.join(os.getenv('CITY_DATA_PATH'), self.labelme_dir, 
                                'labelme/Annotations', folder, annotation_file))

        # image
        imagefile = self.imagefileOfAnnotation (tree.getroot());
        imagepath = op.join(self.labelme_dir, 'labelme/Images', imagefile)
        img = cv2.imread(op.join(os.getenv('CITY_DATA_PATH'), imagepath))
        height, width, depth = img.shape

        deleteAll4imagefile (self.cursor, imagepath)

        # insert the image into the database
        entry = (imagepath, op.basename(folder), width, height)
        self.cursor.execute('''INSERT INTO images(imagefile,src,width,height) 
                               VALUES (?,?,?,?);''', entry)

        img_show = img if self.debug_show else None

        for object_ in tree.getroot().findall('object'):

            # find the name of object. Filter all generic objects
            name = self.parser.parse(object_.find('name').text)
            if name == 'object':
                logging.info('skipped an "object"')
                continue
            if name is None:
                logging.info('skipped a None')
                continue

            # get all the points
            xs, ys = self.pointsOfPolygon(object_)

            # filter out degenerate polygons
            if len(xs) <= 2 or min(xs) == max(xs) or min(ys) == max(ys):
                logging.info ('degenerate polygon ' + str(xs) + ', ' + str(ys))
                continue

            # make bbox
            roi = [min(ys), min(xs), max(ys), max(xs)]

            # make an entry for database
            bbox = roi2bbox (roi)
            entry = (imagepath,
                     name, 
                     bbox[0],
                     bbox[1],
                     bbox[2],
                     bbox[3],
                     0,
                     0)

            # write to db
            self.cursor.execute('''INSERT INTO cars(imagefile,name,x1,y1,width,height,offsetx,offsety) 
                                   VALUES (?,?,?,?,?,?,?,?);''', entry)
            carid = self.cursor.lastrowid
            for i in range(len(xs)):
                self.cursor.execute('''INSERT INTO polygons(carid,x,y) 
                                       VALUES (?,?,?);''', (carid,xs[i],ys[i]))
        self.conn.commit()

        if self.debug_show: 
            cv2.imshow('debug_show', img_show)
            cv2.waitKey(-1)




#
# returns an array of tuples of form (car, car), or (car, None), or (None, car)
#
class PairConverter (BaseConverter):

    def __init__(self, db_path, params):
        BaseConverter.__init__(self, db_path, params)
        self.parser = PairParser()


    def __bypartiteMatch (self, captions_t, captions_b, cars_t, cars_b, file_name):
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


    def processImage (self, folder, annotation_file):

        tree = ET.parse(op.join(os.getenv('CITY_DATA_PATH'), self.labelme_dir, 
                                'labelme/Annotations', folder, annotation_file))

        # image
        imagefile = self.imagefileOfAnnotation (tree.getroot());
        imagepath = op.join(self.labelme_dir, 'labelme/Images', imagefile)
        img = cv2.imread(op.join(os.getenv('CITY_DATA_PATH'), imagepath))
        height, width, depth = img.shape
        halfheight = height / 2

        deleteAll4imagefile (self.cursor, imagepath)

        # insert the image into the database
        entry = (imagepath, op.basename(folder), width, height)
        self.cursor.execute('''INSERT INTO images(imagefile,src,width,height) 
                               VALUES (?,?,?,?);''', entry)

        objects = tree.getroot().findall('object')
        captions_t = []
        captions_b = []
        cars_t = []
        cars_b = []

        # collect captions and assign statuses accordingly
        for object_ in objects:

            # get all the points
            xs, ys = self.pointsOfPolygon(object_)

            # filter out degenerate polygons
            if len(xs) <= 2 or min(xs) == max(xs) or min(ys) == max(ys):
                logging.info ('degenerate polygon ' + str(xs) + ', ' + str(ys))
                continue

            # get bbox and offset ys
            is_top = np.mean(np.mean(ys)) < halfheight
            if is_top:
                roi = [min(ys), min(xs), max(ys), max(xs)]
            else:
                roi = [min(ys)-halfheight, min(xs), max(ys)-halfheight, max(xs)]
                ys = [y-halfheight for y in ys]

            # find the name of object. Filter all generic objects
            (name, number) = self.parser.parse(object_.find('name').text)
            if name is None or number is None:
                logging.info('skipped a None')
                continue

            # make an entry for database
            bbox = roi2bbox (roi)
            entry = (imagepath,
                     name, 
                     bbox[0],
                     bbox[1],
                     bbox[2],
                     bbox[3],
                     0,
                     0 if is_top else halfheight)

            # write car to db
            self.cursor.execute('''INSERT INTO cars(imagefile,name,x1,y1,width,height,offsetx,offsety) 
                                   VALUES (?,?,?,?,?,?,?,?);''', entry)
            carid = self.cursor.lastrowid
            for i in range(len(xs)):
                self.cursor.execute('''INSERT INTO polygons(carid,x,y) 
                                       VALUES (?,?,?);''', (carid,xs[i],ys[i]))
        
            # write to either top or bottom stack
            if is_top:
                captions_t.append((name, number))
                cars_t.append (carid)
            else:
                captions_b.append((name, number))
                cars_b.append (carid)

        pairs = self.__bypartiteMatch (captions_t, captions_b, cars_t, cars_b, annotation_file)

        # write matches to db
        for pair in pairs:
            # take the largest 'match' number
            self.cursor.execute('SELECT MAX(match) FROM matches')
            match = self.cursor.fetchone()[0]
            # logic to process None. The start index in SQL database is 1, not 0
            match = 1 if match is None else match + 1
            # insert
            if pair[0] and not pair[1]:
                self.cursor.execute('INSERT INTO matches(match,carid) VALUES (?,?);', (match,pair[0]))
                self.cursor.execute('INSERT INTO matches(match,carid) VALUES (?,?);', (match,0)) # dummy
            elif pair[1] and not pair[0]:
                self.cursor.execute('INSERT INTO matches(match,carid) VALUES (?,?);', (match,0)) # dummy
                self.cursor.execute('INSERT INTO matches(match,carid) VALUES (?,?);', (match,pair[1]))
            elif pair[0] and pair[1]:
                self.cursor.execute('INSERT INTO matches(match,carid) VALUES (?,?);', (match,pair[0]))
                self.cursor.execute('INSERT INTO matches(match,carid) VALUES (?,?);', (match,pair[1]))


        if not pairs: logging.warning ('file has no valid polygons: ' + annotation_file)

        self.conn.commit()




def folder2frames (folder, db_path, params):

    labelme_dir = params['labelme_dir'] if 'labelme_dir' in params.keys() else ''
    pathlist = glob.glob (op.join(os.getenv('CITY_DATA_PATH'), labelme_dir, 
                                  'labelme/Annotations', folder, '*.xml'))

    with FrameConverter (db_path, params) as converter:
        for path in pathlist:
            logging.debug ('processing file ' + op.basename(path))
            converter.processImage(folder, op.basename(path))



def folder2pairs (folder, db_path, params):

    labelme_dir = params['labelme_dir'] if 'labelme_dir' in params.keys() else ''
    pathlist = glob.glob (op.join(os.getenv('CITY_DATA_PATH'), labelme_dir, 
                                  'labelme/Annotations', folder, '*.xml'))

    with PairConverter (db_path, params) as converter:
        for path in pathlist:
            logging.debug ('processing file ' + op.basename(path))
            converter.processImage(folder, op.basename(path))



    