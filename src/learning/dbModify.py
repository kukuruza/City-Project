import math
import numpy as np
import cv2
from datetime import datetime
import os, sys
import collections
import logging
import os.path as op
import glob
import shutil
import sqlite3
from dbInterface import deleteCar, queryField, checkTableExists, getImageField
import dbInterface
import utilities
from utilities import bbox2roi, roi2bbox, bottomCenter, expandRoiFloat, expandRoiToRatio, drawRoi
import matplotlib.pyplot as plt  # for colormaps
from dbBase import BaseProcessor


def isPolygonAtBorder (xs, ys, width, height, params):
    border_thresh = (height + width) / 2 * params['border_thresh_perc']
    dist_to_border = min (xs, [width - x for x in xs], ys, [height - y for y in ys])
    num_too_close = sum([x < border_thresh for x in dist_to_border])
    return num_too_close >= 2


def isRoiAtBorder (roi, width, height, params):
    border_thresh = (height + width) / 2 * params['border_thresh_perc']
    return min (roi[0], roi[1], height+1 - roi[2], width+1 - roi[3]) < border_thresh


def sizeProb (roi, params):
    # naive definition of size
    size = ((roi[2] - roi[0]) + (roi[3] - roi[1])) / 2
    bc = bottomCenter(roi)
    max_prob = params['size_map'][bc[0], bc[1]]
    prob = utilities.gammaProb (size, max_prob, params['size_acceptance'])
    if size < params['min_width_thresh']: prob = 0
    logging.debug ('size of roi probability: ' + str(prob))
    return prob


def ratioProb (roi, params):
    ratio = float(roi[2] - roi[0]) / (roi[3] - roi[1])   # height / width
    prob = utilities.gammaProb (ratio, 1.333, params['ratio_acceptance'])
    logging.debug ('ratio of roi probability: ' + str(prob))
    return prob



def __filterBorderCar__ (c, car_entry, params):

    carid = queryField(car_entry, 'id')
    roi = bbox2roi (queryField(car_entry, 'bbox'))
    imagefile = queryField(car_entry, 'imagefile')

    c.execute('SELECT width,height FROM images WHERE imagefile=?', (imagefile,))
    (width,height) = c.fetchone()

    border_prob = 1
    if checkTableExists(c, 'polygons'):
        # get polygon
        c.execute('SELECT x,y FROM polygons WHERE carid=?', (carid,))
        polygon_entries = c.fetchall()
        xs = [polygon_entry[0] for polygon_entry in polygon_entries]
        ys = [polygon_entry[1] for polygon_entry in polygon_entries]
        assert (len(xs) > 2 and min(xs) != max(xs) and min(ys) != max(ys))
        # filter border
        if isPolygonAtBorder(xs, ys, width, height, params): 
            logging.info ('border polygon ' + str(xs) + ', ' + str(ys))
            border_prob = 0
    else:
        # filter border
        if isRoiAtBorder(roi, width, height, params): 
            logging.info ('border polygon ' + str(roi))
            border_prob = 0

    # get current score
    c.execute('SELECT name,score FROM cars WHERE id=?', (carid,))
    (name,score) = c.fetchone()
    if score is None: score = 1.0 

    # update score in db
    score *= border_prob
    c.execute('UPDATE cars SET score=? WHERE id=?', (score,carid))

    if params['debug_show']:
        color = tuple([int(x * 255) for x in plt.cm.jet(score)][0:3])
        drawRoi (params['img_show'], roi, '', color)



def __filterRatioCar__ (c, car_entry, params):

    carid = queryField(car_entry, 'id')
    roi = bbox2roi (queryField(car_entry, 'bbox'))
    imagefile = queryField(car_entry, 'imagefile')

    # get current score
    c.execute('SELECT name,score FROM cars WHERE id=?', (carid,))
    (name,score) = c.fetchone()
    if score is None: score = 1.0 

    # get probabilities of car, given constraints
    ratio_prob = ratioProb(roi, params)
    
    # update score in db
    score *= ratio_prob
    c.execute('UPDATE cars SET score=? WHERE id=?', (score,carid))

    if params['debug_show']:
        color = tuple([int(x * 255) for x in plt.cm.jet(score)][0:3])
        drawRoi (params['img_show'], roi, '', color)



def __filterSizeCar__ (c, car_entry, params):

    carid = queryField(car_entry, 'id')
    roi = bbox2roi (queryField(car_entry, 'bbox'))
    imagefile = queryField(car_entry, 'imagefile')

    # get current score
    c.execute('SELECT name,score FROM cars WHERE id=?', (carid,))
    (name,score) = c.fetchone()
    if score is None: score = 1.0 

    # get probabilities of car, given constraints
    size_prob = sizeProb (roi, params)
    
    # update score in db
    score *= size_prob
    c.execute('UPDATE cars SET score=? WHERE id=?', (score,carid))

    if params['debug_show']:
        color = tuple([int(x * 255) for x in plt.cm.jet(score)][0:3])
        drawRoi (params['img_show'], roi, '', color)



def __expandCarBbox__ (c, car_entry, params):

    expand_perc = params['expand_perc']
    target_ratio = params['target_ratio']
    carid = queryField(car_entry, 'id')
    roi = bbox2roi (queryField(car_entry, 'bbox'))
    imagefile = queryField(car_entry, 'imagefile')

    c.execute('SELECT height, width FROM images WHERE imagefile=?', (imagefile,))
    (height, width) = c.fetchone()

    old = list(roi)
    if params['keep_ratio']:
        roi = expandRoiToRatio (roi, (height, width), expand_perc, target_ratio)
    else:
        roi = expandRoiFloat (roi, (height, width), (expand_perc, expand_perc))

    if params['debug_show']:
        imagepath = op.join (os.getenv('CITY_DATA_PATH'), imagefile)
        if not op.exists (imagepath):
            raise Exception ('image does not exist: ' + imagepath)
        img_show = cv2.imread(imagepath)
        drawRoi (img_show, old, '', (0,0,255))
        drawRoi (img_show, roi, '', (255,0,0))
        cv2.imshow('debug_show', img_show)
        if cv2.waitKey(-1) == 27: 
            cv2.destroyWindow('debug_show')
            params['debug_show'] = False

    c.execute('''UPDATE cars SET x1=?, y1=?, width=?, height=? 
                 WHERE id=?''', tuple (roi2bbox(roi) + [carid]))



def __clusterBboxes__ (c, imagefile, params):

    # TODO: now assigned 'vehicle' to all names, angles and color are reset to null

    c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
    car_entries = c.fetchall()
    logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

    # collect rois
    rois = []
    scores = []
    for car_entry in car_entries:
        carid = queryField(car_entry, 'id')
        roi = bbox2roi (queryField(car_entry, 'bbox'))
        score = queryField(car_entry, 'score')
        rois.append (roi)
        scores.append (score)

    # cluster rois
    #params['scores'] = scores
    rois_clustered, clusters, scores = utilities.hierarchicalClusterRoi (rois, params)

    # show
    if params['debug_show']:
        imagepath = op.join (os.getenv('CITY_DATA_PATH'), imagefile)
        if not op.exists (imagepath):
            raise Exception ('image does not exist: ' + imagepath)
        img_show = cv2.imread(imagepath)
        for roi in rois:
            drawRoi (img_show, roi, '', (0,0,255))
        for roi in rois_clustered:
            drawRoi (img_show, roi, '', (255,0,0))
        cv2.imshow('debug_show', img_show)
        if cv2.waitKey(-1) == 27: 
            cv2.destroyWindow('debug_show')
            params['debug_show'] = False

    # update db
    for car_entry in car_entries:
        deleteCar (c, queryField(car_entry, 'id'))
    for i in range(len(rois_clustered)):
        roi = rois_clustered[i]
        score = scores[i]
        bbox = roi2bbox(roi)
        entry = (imagefile, 'vehicle', bbox[0], bbox[1], bbox[2], bbox[3], score)
        c.execute('''INSERT INTO cars(imagefile,name,x1,y1,width,height,score) 
                     VALUES (?,?,?,?,?,?,?);''', entry)








class ModifyProcessor (BaseProcessor):


    def filterBorder (self, params):
        logging.info ('==== filterBorder ====')
        c = self.cursor

        params = self.setParamUnlessThere (params, 'border_thresh_perc', 0.03)
        params = self.setParamUnlessThere (params, 'debug_show',         False)
        params = self.setParamUnlessThere (params, 'constraint',     '')

        c.execute('SELECT imagefile FROM images')
        image_entries = c.fetchall()

        for (imagefile,) in image_entries:

            imagepath = op.join (self.CITY_DATA_PATH, imagefile)
            if not op.exists (imagepath):
                raise Exception ('image does not exist: ' + imagepath)
            params['img_show'] = cv2.imread(imagepath) if params['debug_show'] else None

            c.execute('SELECT * FROM cars WHERE imagefile=? ' + params['constraint'], (imagefile,))
            car_entries = c.fetchall()
            logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

            for car_entry in car_entries:
                __filterCar__ (c, car_entry, params)

            if params['debug_show'] and 'button' in locals() and button != 27: 
                cv2.imshow('debug_show', params['img_show'])
                button = cv2.waitKey(-1)
                if button == 27: cv2.destroyWindow('debug_show')

        return self



    def filterRatio (self, params):
        logging.info ('==== filterRatio ====')
        c = self.cursor

        params = self.setParamUnlessThere (params, 'ratio_acceptance', 3)
        params = self.setParamUnlessThere (params, 'debug_show',       False)
        params = self.setParamUnlessThere (params, 'constraint',       '')

        c.execute('SELECT imagefile FROM images')
        image_entries = c.fetchall()

        for (imagefile,) in image_entries:

            imagepath = op.join (self.CITY_DATA_PATH, imagefile)
            if not op.exists (imagepath):
                raise Exception ('image does not exist: ' + imagepath)
            params['img_show'] = cv2.imread(imagepath) if params['debug_show'] else None

            c.execute('SELECT * FROM cars WHERE imagefile=? ' + params['constraint'], (imagefile,))
            car_entries = c.fetchall()
            logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

            for car_entry in car_entries:
                __filterRatioCar__ (c, car_entry, params)

            if params['debug_show'] and 'button' in locals() and button != 27: 
                cv2.imshow('debug_show', params['img_show'])
                button = cv2.waitKey(-1)
                if button == 27: cv2.destroyWindow('debug_show')

        return self



    def filterSize (self, size_map_path, params):
        logging.info ('==== filterSize ====')
        c = self.cursor

        params = self.setParamUnlessThere (params, 'min_width_thresh', 10)
        params = self.setParamUnlessThere (params, 'size_acceptance',  3)
        params = self.setParamUnlessThere (params, 'sizemap_dilate',   21)
        params = self.setParamUnlessThere (params, 'debug_show',       False)
        params = self.setParamUnlessThere (params, 'debug_sizemap',    False)
        params = self.setParamUnlessThere (params, 'constraint',       '')

        size_map_path  = op.join(self.CITY_DATA_PATH, size_map_path)
        params['size_map'] = cv2.imread (size_map_path, 0).astype(np.float32)

        if params['debug_sizemap']:
            cv2.imshow ('size_map original', params['size_map'])

        # dilate size_map
        kernel = np.ones ((params['sizemap_dilate'], params['sizemap_dilate']), 'uint8')
        params['size_map'] = cv2.dilate (params['size_map'], kernel)

        if params['debug_sizemap']:
            cv2.imshow ('size_map dilated', params['size_map'])
            cv2.waitKey(-1)

        c.execute('SELECT imagefile FROM images')
        image_entries = c.fetchall()

        for (imagefile,) in image_entries:

            imagepath = op.join (self.CITY_DATA_PATH, imagefile)
            if not op.exists (imagepath):
                raise Exception ('image does not exist: ' + imagepath)
            params['img_show'] = cv2.imread(imagepath) if params['debug_show'] else None

            c.execute('SELECT * FROM cars WHERE imagefile=? ' + params['constraint'], (imagefile,))
            car_entries = c.fetchall()
            logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

            for car_entry in car_entries:
                __filterSizeCar__ (c, car_entry, params)

            if params['debug_show'] and 'button' in locals() and button != 27: 
                cv2.imshow('debug_show', params['img_show'])
                button = cv2.waitKey(-1)
                if button == 27: cv2.destroyWindow('debug_show')

        return self



    def thresholdScore (self, params = {}):
        logging.info ('==== thresholdScore ====')
        c = self.cursor

        params = self.setParamUnlessThere (params, 'threshold', 0.5)

        c.execute('SELECT id,score FROM cars')
        car_entries = c.fetchall()

        for (carid,score) in car_entries:
            if score < params['threshold']:
                c.execute('DELETE FROM cars WHERE id = ?', (carid,))

        return self



    def expandBboxes (self, params):
        logging.info ('==== expandBboxes ====')
        c = self.cursor

        params = self.setParamUnlessThere (params, 'expand_perc', 0.1)
        params = self.setParamUnlessThere (params, 'target_ratio', 0.75)  # h / w
        params = self.setParamUnlessThere (params, 'keep_ratio', True)
        params = self.setParamUnlessThere (params, 'debug_show', False)

        c.execute('SELECT imagefile FROM images')
        image_entries = c.fetchall()

        for (imagefile,) in image_entries:

            c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
            car_entries = c.fetchall()
            logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

            for car_entry in car_entries:
                __expandCarBbox__ (c, car_entry, params)

        return self



    def clusterBboxes (self, params = {}):
        logging.info ('==== clusterBboxes ====')
        c = self.cursor

        params = self.setParamUnlessThere (params, 'threshold', 0.2)
        params = self.setParamUnlessThere (params, 'debug_show', False)

        c.execute('SELECT imagefile FROM images')
        image_entries = c.fetchall()

        for (imagefile,) in image_entries:
            __clusterBboxes__ (c, imagefile, params)

        return self



    def assignOrientations (self, params):
        logging.info ('==== assignOrientations ====')
        c = self.cursor

        if 'size_map_path' not in params.keys():
            raise Exception ('size_map_path is not given in params')
        if 'pitch_map_path' not in params.keys():
            raise Exception ('pitch_map_path is not given in params')
        if 'yaw_map_path' not in params.keys():
            raise Exception ('yaw_map_path is not given in params')

        size_map_path  = op.join(self.CITY_DATA_PATH, params['size_map_path'])
        pitch_map_path = op.join(self.CITY_DATA_PATH, params['pitch_map_path'])
        yaw_map_path   = op.join(self.CITY_DATA_PATH, params['yaw_map_path'])
        if not op.exists(size_map_path):
            raise Exception ('size_map_path does not exist: ' + size_map_path)
        if not op.exists(pitch_map_path):
            raise Exception ('pitch_map_path does not exist: ' + pitch_map_path)
        if not op.exists(yaw_map_path):
            raise Exception ('yaw_map_path does not exist: ' + yaw_map_path)
        size_map  = cv2.imread (size_map_path, 0).astype(np.float32)
        pitch_map = cv2.imread (pitch_map_path, 0).astype(np.float32)
        yaw_map   = cv2.imread (yaw_map_path, -1).astype(np.float32)
        # in the tiff angles belong to [0, 360). Change that to [-180, 180)
        yaw_map   = np.add(-180, np.mod( np.add(180, yaw_map), 360 ) )


        c.execute('SELECT * FROM cars')
        car_entries = c.fetchall()

        for car_entry in car_entries:
            carid = queryField (car_entry, 'id')
            roi = bbox2roi (queryField (car_entry, 'bbox'))
            bc = bottomCenter(roi)
            if size_map[bc[0], bc[1]] > 0:
                yaw   = float(yaw_map   [bc[0], bc[1]])
                pitch = float(pitch_map [bc[0], bc[1]])
                c.execute('UPDATE cars SET yaw=?, pitch=? WHERE id=?', (yaw, pitch, carid))

        return self



    def moveDir (self, params):
        logging.info ('==== moveDir ====')
        c = self.cursor

        if 'images_dir' in params.keys():

            c.execute('SELECT imagefile FROM images')
            imagefiles = c.fetchall()

            for (oldfile,) in imagefiles:
                # op.basename (op.dirname(oldfile)), 
                newfile = op.join (params['images_dir'], op.basename (oldfile))
                c.execute('UPDATE images SET imagefile=? WHERE imagefile=?', (newfile, oldfile))
                c.execute('UPDATE cars SET imagefile=? WHERE imagefile=?', (newfile, oldfile))

        if 'ghosts_dir' in params.keys():

            c.execute('SELECT ghostfile FROM images ')
            ghostfiles = c.fetchall()

            for (oldfile,) in ghostfiles:
                # op.basename (op.dirname(oldfile)), 
                newfile = op.join (params['ghosts_dir'], op.basename (oldfile))
                c.execute('UPDATE images SET ghostfile=? WHERE ghostfile=?', (newfile, oldfile))

        if 'masks_dir' in params.keys():

            c.execute('SELECT maskfile FROM images')
            maskfiles = c.fetchall()

            for (oldfile,) in maskfiles:
                # op.basename (op.dirname(oldfile)), 
                newfile = op.join (params['masks_dir'], op.basename (oldfile))
                c.execute('UPDATE images SET maskfile=? WHERE maskfile=?', (newfile, oldfile))

        return self


        
    def merge (self, db_add_path, params = {}):
        logging.info ('==== merge ====')
        c = self.cursor

        db_add_path  = op.join(self.CITY_DATA_PATH, db_out_path)

        conn_add = sqlite3.connect (db_add_path)
        cursor_add = conn_add.cursor()

        # copy images
        cursor_add.execute('SELECT * FROM images')
        image_entries = cursor_add.fetchall()

        for image_entry in image_entries:
            imagefile = image_entry[0]
            # check that doesn't exist
            c.execute('SELECT count(*) FROM images WHERE imagefile=?', (imagefile,))
            (num,) = c.fetchone()
            if num > 0:
                logging.info ('duplicate image ' + imagefile + ' found in ' + db_in_paths[1]) 
                continue
            # insert image
            c.execute('INSERT INTO images VALUES (?,?,?,?,?,?,?);', image_entry)
        
        # copy cars
        cursor_add.execute('SELECT * FROM cars')
        car_entries = cursor_add.fetchall()

        for car_entry in car_entries:
            carid = queryField (car_entry, 'id')
            s = 'cars(imagefile,name,x1,y1,width,height,score,yaw,pitch,color)'
            c.execute('INSERT INTO ' + s + ' VALUES (?,?,?,?,?,?,?,?,?,?);', car_entry[1:])

        conn_add.close()
        return self



    def maskScores (self, params = {}):
        logging.info ('==== maskScores ====')
        c = self.cursor

        # load the map of scores and normalize it by 1/255
        if 'score_map_path' not in params.keys():
            raise Exception ('score_map_path is not given in params')
        score_map_path = op.join(self.CITY_DATA_PATH, params['score_map_path'])
        if not op.exists(score_map_path):
            raise Exception ('score_map_path does not exist: ' + score_map_path)
        score_map = cv2.imread(score_map_path, -1).astype(float);
        score_map /= 255.0

        c.execute('SELECT * FROM cars')
        car_entries = c.fetchall()

        for car_entry in car_entries:
            carid = queryField (car_entry, 'id')
            bbox  = queryField (car_entry, 'bbox')
            score = queryField (car_entry, 'score')
            if not score: score = 1 

            center = bottomCenter(bbox2roi(bbox))
            score *= score_map[center[0], center[1]]
            c.execute('UPDATE cars SET score=? WHERE id=?', (score, carid))

        return self



    def polygonsToMasks (self, params = {}):
        logging.info ('==== polygonsToMasks ====')
        c = self.cursor

        c.execute('SELECT * FROM images')
        image_entries = c.fetchall()

        imagefile = getImageField (image_entries[0], 'imagefile')
        folder = op.basename(op.dirname(imagefile))
        labelme_dir = op.dirname(op.dirname(op.dirname(imagefile)))
        maskdir = op.join(self.CITY_DATA_PATH, labelme_dir, 'Masks', folder)
        if op.exists (maskdir): 
            shutil.rmtree (maskdir) 
        os.mkdir (maskdir)

        # copy images and possibly masks
        for image_entry in image_entries:

            imagefile = getImageField (image_entry, 'imagefile')
            imagename = op.basename(imagefile)
            maskname = op.splitext(imagename)[0] + '.png'
            folder = op.basename(op.dirname(imagefile))
            labelme_dir = op.dirname(op.dirname(op.dirname(imagefile)))
            maskfile = op.join(labelme_dir, 'Masks', folder, maskname)

            c.execute('UPDATE images SET maskfile=? WHERE imagefile=?', (maskfile, imagefile))

            height = getImageField (image_entry, 'height')
            width = getImageField (image_entry, 'width')
            mask = np.zeros((height, width), dtype=np.uint8)

            c.execute('SELECT id FROM cars WHERE imagefile=?', (imagefile,))
            for (carid,) in c.fetchall():
                c.execute('SELECT x,y FROM polygons WHERE carid = ?', (carid,))
                polygon_entries = c.fetchall()
                pts = [[pt[0], pt[1]] for pt in polygon_entries]
                cv2.fillConvexPoly(mask, np.asarray(pts, dtype=np.int32), 255)
        
            logging.info ('saving mask to file: ' + maskfile)
            cv2.imwrite (op.join(self.CITY_DATA_PATH, maskfile), mask)

        return self




    def dbCustomScript (self, params = {}):
        c = self.cursor

        logging.error ('dbCustomScript currently empty')

        return self
