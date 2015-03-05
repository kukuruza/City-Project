#!/bin/python

import numpy as np
import cv2
import xml.etree.ElementTree as ET
import os, sys
import collections
import logging
import os.path as OP
import glob
import shutil
import sqlite3


sys.path.insert(0, os.path.abspath('annotations'))
from annotations.parser import FrameParser, PairParser


#
# roi - all inclusive, like in Matlab
# crop = im[roi[0]:roi[2]+1, roi[1]:roi[3]+1] (differs from Matlab)
#
def roi2bbox (roi):
    assert (isinstance(roi, list) and len(roi) == 4)
    return [roi[1], roi[0], roi[3]-roi[1]+1, roi[2]-roi[0]+1]


# formula for bottom-center
def bottomCenter (roi):
    return (roi[0] * 0.25 + roi[2] * 0.75, roi[1] * 0.5 + roi[3] * 0.5)


#
# expandRoiFloat expands a ROI, and clips it within borders
#
def expandRoiFloat (roi, (imheight, imwidth), (perc_y, perc_x)):
    half_delta_y = float(roi[2] + 1 - roi[0]) * perc_y / 2
    half_delta_x = float(roi[3] + 1 - roi[1]) * perc_x / 2
    # expand each side
    roi[0] -= half_delta_y
    roi[1] -= half_delta_x
    roi[2] += half_delta_y
    roi[3] += half_delta_x
    # make integer
    roi = [int(x) for x in roi]
    # move to clip into borders
    if roi[0] < 0:
        roi[2] += abs(roi[0])
        roi[0] = 0
    if roi[1] < 0:
        roi[3] += abs(roi[1])
        roi[1] = 0
    if roi[2] > imheight-1:
        roi[0] -= abs((imheight-1) - roi[2])
        roi[2] = imheight-1
    if roi[3] > imwidth-1:
        roi[1] -= abs((imwidth-1) - roi[3])
        roi[3] = imwidth-1
    # check that now averything is within borders (bbox is not too big)
    assert (roi[0] >= 0 and roi[1] >= 0)
    assert (roi[2] <= imheight-1 and roi[3] <= imwidth-1)
    return roi


#
# expands a ROI to keep 'ratio', and maybe more, up to 'expand_perc'
#
def expandRoiToRatio (roi, (imheight, imwidth), expand_perc, ratio):
    # adjust width and height to ratio
    height = float(roi[2] + 1 - roi[0])
    width  = float(roi[3] + 1 - roi[1])
    if height / width < ratio:
       perc = ratio * width / height - 1
       roi = expandRoiFloat (roi, (imheight, imwidth), (perc, 0))
    else:
       perc = height / width / ratio - 1
       roi = expandRoiFloat (roi, (imheight, imwidth), (0, perc))
    # additional expansion
    perc = expand_perc - perc
    if perc > 0:
        roi = expandRoiFloat (roi, (imheight, imwidth), (perc, perc))
    return roi





class BaseAnalyzer:

    border_thresh_perc = 0.03
    expand_perc = 0.1
    target_ratio = 0.75   # width / height
    keep_ratio = False
    size_acceptance = (0.4, 2)
    ratio_acceptance = 2
    sizemap_dilate = 21
    debug_show = False

    def __init__(self, params):
        if 'border_thresh_perc' in params.keys(): 
            self.border_thresh_perc = params['border_thresh_perc']
        if 'expand_perc' in params.keys(): 
            self.expand_perc = params['expand_perc']
        if 'target_ratio' in params.keys(): 
            self.target_ratio = params['target_ratio']
        if 'keep_ratio' in params.keys(): 
            self.keep_ratio = params['keep_ratio']
        if 'size_acceptance' in params.keys(): 
            self.size_acceptance = params['size_acceptance']
        if 'ratio_acceptance' in params.keys(): 
            self.ratio_acceptance = params['ratio_acceptance']
        if 'sizemap_dilate' in params.keys(): 
            self.sizemap_dilate = params['sizemap_dilate']
        if 'debug_show' in params.keys():
            self.debug_show = params['debug_show']
        if 'debug_sizemap' in params.keys(): debug_sizemap = params['debug_sizemap']
        else: debug_sizemap = False

        if 'geom_maps_dir' in params.keys():
            self.loadMaps (params['geom_maps_dir'])
        else:
            raise Exception ('BaseAnalyzer: geom_maps_dir is not given in params')
        if 'labelme_data_path' in params.keys():
            self.labelme_data_path = params['labelme_data_path']
        else:
            raise Exception ('BaseAnalyzer: labelme_data_path is not given in params')

        if debug_sizemap:
            cv2.imshow ('size_map original', self.size_map)

        # dilate size_map
        kernel = np.ones ((self.sizemap_dilate, self.sizemap_dilate), 'uint8')
        self.size_map = cv2.dilate (self.size_map, kernel)

        if debug_sizemap:
            cv2.imshow ('size_map dilated', self.size_map)
            cv2.waitKey(-1)



    # this function knows all about size- and orientation- maps
    def loadMaps (self, geom_maps_dir):
        size_map_path  = OP.join (geom_maps_dir, 'sizeMap.tiff')
        pitch_map_path = OP.join (geom_maps_dir, 'pitchMap.tiff')
        yaw_map_path   = OP.join (geom_maps_dir, 'yawMap.tiff')
        self.size_map  = cv2.imread (size_map_path, 0).astype(np.float32)
        self.pitch_map = cv2.imread (pitch_map_path, 0).astype(np.float32)
        self.yaw_map   = cv2.imread (yaw_map_path, -1).astype(np.float32)
        self.yaw_map   = cv2.add (self.yaw_map, -360)


    def imagefileOfAnnotation (self, annotation):
        folder = annotation.find('folder').text
        imagename = annotation.find('filename').text
        imagepath = OP.join (self.labelme_data_path, 'Images', folder, imagename)
        if not OP.exists (imagepath):
            raise Exception ('no image at path ' + imagepath)
        return OP.join (folder, imagename)

    
    def pointsOfPolygon (self, annotation):
        pts = annotation.find('polygon').findall('pt')
        xs = []
        ys = []
        for pt in pts:
            xs.append( int(pt.find('x').text) )
            ys.append( int(pt.find('y').text) )
        return xs, ys


    def isDegeneratePolygon (self, xs, ys):
        return len(xs) <= 2 or min(xs) == max(xs) or min(ys) == max(ys)


    def isPolygonAtBorder (self, xs, ys, width, height):
        border_thresh = (height + width) / 2 * self.border_thresh_perc
        dist_to_border = min (xs, [width - x for x in xs], ys, [height - y for y in ys])
        num_too_close = sum([x < border_thresh for x in dist_to_border])
        return num_too_close >= 2


    def isWrongSize (self, roi):
        bc = bottomCenter(roi)
        # whatever definition of size
        size = ((roi[2] - roi[0]) + (roi[3] - roi[1])) / 2
        return self.size_map [bc[0], bc[1]] * self.size_acceptance[0] > size or \
               self.size_map [bc[0], bc[1]] * self.size_acceptance[1] < size


    def isBadRatio (self, roi):
        ratio = float(roi[2] - roi[0]) / (roi[3] - roi[1])   # height / width
        return self.target_ratio / self.ratio_acceptance > ratio or \
               self.target_ratio * self.ratio_acceptance < ratio


    def assignOrientation (self, roi):
        bc = bottomCenter(roi)
        # get corresponding yaw-pitch
        yaw   = self.yaw_map   [bc[0], bc[1]]
        pitch = self.pitch_map [bc[0], bc[1]]
        return (float(yaw), float(pitch))


    def debugShowAddRoi (self, img, roi, color):
        if self.debug_show: 
            cv2.rectangle (img, (roi[1], roi[0]), (roi[3], roi[2]), color)




class FrameAnalyzer (BaseAnalyzer):

    def __init__(self, db_path, params):
        BaseAnalyzer.__init__(self, params)

        self.parser = FrameParser()

        self.conn = sqlite3.connect (db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS cars
                             (id INTEGER PRIMARY KEY,
                              imagefile TEXT, 
                              name TEXT, 
                              x1 INTEGER,
                              y1 INTEGER,
                              width INTEGER, 
                              height INTEGER,
                              offsetx INTEGER,
                              offsety INTEGER,
                              yaw REAL,
                              pitch REAL
                              );''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS polygons
                             (id INTEGER PRIMARY KEY,
                              carid TEXT, 
                              x INTEGER,
                              y INTEGER
                              );''')
        
        self.conn.commit()


    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.conn.close()



    def processImage (self, folder, annotation_file):

        tree = ET.parse(OP.join(self.labelme_data_path, 'Annotations', folder, annotation_file))

        # image, backimage, and ghost
        imagefile = self.imagefileOfAnnotation (tree.getroot());
        imagepath = OP.join (self.labelme_data_path, 'Images', imagefile)
        img = cv2.imread(imagepath)
        height, width, depth = img.shape

        # delete cars from this imagefile from all tables
        self.cursor.execute('SELECT id FROM cars WHERE imagefile=(?);', (imagefile,));
        carids = self.cursor.fetchall()
        carids = [str(carid[0]) for carid in carids]
        carids_str = '(' + ','.join(carids) + ')'
        self.cursor.execute('DELETE FROM cars     WHERE id IN ' + carids_str);
        self.cursor.execute('DELETE FROM polygons WHERE carid IN ' + carids_str);
        #sself.cursor.execute('DELETE FROM matches  WHERE carid IN ' + carids_str);
        logging.debug ('delete cars, polygons, matches from table: ' + ','.join(carids))

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

            # make bbox
            roi = [min(ys), min(xs), max(ys), max(xs)]

            # filter bad ones
            if self.isDegeneratePolygon(xs, ys): 
                logging.info ('degenerate polygon ' + str(xs) + ', ' + str(ys))
                self.debugShowAddRoi (img_show, roi, (0,0,255))
                continue
            if self.isPolygonAtBorder(xs, ys, width, height): 
                logging.info ('border polygon ' + str(xs) + ', ' + str(ys))
                self.debugShowAddRoi (img_show, roi, (0,0,255))
                continue
            if self.isWrongSize(roi):
                logging.info ('wrong size of polygon ' + str(xs) + ', ' + str(ys))
                self.debugShowAddRoi (img_show, roi, (0,0,255))
                continue
            if self.isBadRatio(roi):
                logging.info ('bad ratio of polygon ' + str(xs) + ', ' + str(ys))
                self.debugShowAddRoi (img_show, roi, (0,0,255))
                continue

            # expand bbox
            if self.keep_ratio:
                roi = expandRoiToRatio (roi, (height, width), self.expand_perc, self.target_ratio)
            else:
                roi = expandRoiFloat (roi, (height, width), (self.expand_perc, self.expand_perc))

            self.debugShowAddRoi (img_show, roi, (255,0,0))

            # make an entry for database
            bbox = roi2bbox (roi)
            (yaw, pitch) = self.assignOrientation (roi)
            entry = (imagefile,
                     name, 
                     bbox[0],
                     bbox[1],
                     bbox[2],
                     bbox[3],
                     0,
                     0,
                     yaw,
                     pitch)

            # write to db
            self.cursor.execute('''INSERT INTO cars(imagefile,name,x1,y1,width,height,offsetx,offsety,yaw,pitch) 
                                   VALUES (?,?,?,?,?,?,?,?,?,?);''', entry)
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
class PairAnalyzer (BaseAnalyzer):

    def __init__(self, db_path, params):
        BaseAnalyzer.__init__(self, params)

        self.parser = PairParser()

        self.conn = sqlite3.connect (db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS cars
                             (id INTEGER PRIMARY KEY,
                              imagefile TEXT, 
                              name TEXT, 
                              x1 INTEGER,
                              y1 INTEGER,
                              width INTEGER, 
                              height INTEGER,
                              offsetx INTEGER,
                              offsety INTEGER,
                              yaw REAL,
                              pitch REAL
                              );''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS polygons
                             (id INTEGER PRIMARY KEY,
                              carid TEXT, 
                              x INTEGER,
                              y INTEGER
                              );''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS matches
                             (id INTEGER PRIMARY KEY,
                              match INTEGER,
                              carid INTEGER
                              );''')

        self.conn.commit()


    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.conn.close()




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

        tree = ET.parse(OP.join(self.labelme_data_path, 'Annotations', folder, annotation_file))

        # image, backimage, and ghost
        imagefile = self.imagefileOfAnnotation (tree.getroot());
        imagepath = OP.join (self.labelme_data_path, 'Images', imagefile)
        img = cv2.imread(imagepath)
        height, width, depth = img.shape
        halfheight = height / 2

        objects = tree.getroot().findall('object')
        captions_t = []
        captions_b = []
        cars_t = []
        cars_b = []

        # delete cars from this imagefile from all tables
        self.cursor.execute('SELECT id FROM cars WHERE imagefile=(?);', (imagefile,));
        carids = self.cursor.fetchall()
        carids = [str(carid[0]) for carid in carids]
        carids_str = '(' + ','.join(carids) + ')'
        self.cursor.execute('DELETE FROM cars     WHERE id IN ' + carids_str);
        self.cursor.execute('DELETE FROM polygons WHERE carid IN ' + carids_str);
        self.cursor.execute('SELECT match FROM matches WHERE carid IN ' + carids_str);
        matches = self.cursor.fetchall()
        matches = [str(match[0]) for match in matches]
        matches_str = '(' + ','.join(matches) + ')'
        self.cursor.execute('DELETE FROM matches  WHERE match IN ' + matches_str);
        logging.debug ('delete cars, polygons, matches from table: ' + ','.join(carids))

        # collect captions and assign statuses accordingly
        for object_ in objects:

            # get all the points
            xs, ys = self.pointsOfPolygon(object_)

            # get bbox and offset ys
            is_top = np.mean(np.mean(ys)) < halfheight
            if is_top:
                roi = [min(ys), min(xs), max(ys), max(xs)]
            else:
                roi = [min(ys)-halfheight, min(xs), max(ys)-halfheight, max(xs)]
                ys = [y-halfheight for y in ys]

            # filter bad ones (the border polygons are NOT filtered)
            if self.isDegeneratePolygon(xs, ys): 
                logging.info ('degenerate polygon ' + str(xs) + ', ' + str(ys))
                continue
            if self.isWrongSize(roi):
                logging.info ('wrong size of polygon ' + str(xs) + ', ' + str(ys))
                continue
            if self.isBadRatio(roi):
                logging.info ('bad ratio of polygon ' + str(xs) + ', ' + str(ys))
                continue

            # expand bbox
            if self.keep_ratio:
                roi = expandRoiToRatio (roi, (halfheight, width), self.expand_perc, self.target_ratio)
            else:
                roi = expandRoiFloat (roi, (halfheight, width), (self.expand_perc, self.expand_perc))

            # find the name of object. Filter all generic objects
            (name, number) = self.parser.parse(object_.find('name').text)
            if name is None or number is None:
                logging.info('skipped a None')
                continue

            # make an entry for database
            bbox = roi2bbox (roi)
            (yaw, pitch) = self.assignOrientation (roi)
            entry = (imagefile,
                     name, 
                     bbox[0],
                     bbox[1],
                     bbox[2],
                     bbox[3],
                     0,
                     0 if is_top else halfheight,
                     yaw,
                     pitch)

            # write car to db
            self.cursor.execute('''INSERT INTO cars(imagefile,name,x1,y1,width,height,offsetx,offsety,yaw,pitch) 
                                   VALUES (?,?,?,?,?,?,?,?,?,?);''', entry)
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

    labelme_data_path = params['labelme_data_path']
    pathlist = glob.glob (OP.join(labelme_data_path, 'Annotations', folder, '*.xml'))

    with FrameAnalyzer (db_path, params) as analyzer:
        for path in pathlist:
            logging.debug ('processing file ' + OP.basename(path))
            analyzer.processImage(folder, OP.basename(path))




def folder2pairs (folder, db_path, params):

    labelme_data_path = params['labelme_data_path']
    pathlist = glob.glob (OP.join(labelme_data_path, 'Annotations', folder, '*.xml'))

    with PairAnalyzer (db_path, params) as analyzer:
        for path in pathlist:
            logging.debug ('processing file ' + OP.basename(path))
            analyzer.processImage(folder, OP.basename(path))



    