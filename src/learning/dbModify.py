import os, sys, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/backend'))
import math
import numpy as np
import cv2
from datetime import datetime
import collections
import logging
import glob
import shutil
import sqlite3
from helperDb import deleteCar, carField, imageField
import helperDb
import utilities
from utilities import bbox2roi, roi2bbox, bottomCenter, expandRoiFloat, expandRoiToRatio, drawRoi
import helperSetup
import helperKeys
import helperImg


def isPolygonAtBorder (xs, ys, width, height, params):
    border_thresh = (height + width) / 2 * params['border_thresh_perc']
    dist_to_border = min (xs, [width - x for x in xs], ys, [height - y for y in ys])
    num_too_close = sum([x < border_thresh for x in dist_to_border])
    return num_too_close >= 2


def isRoiAtBorder (roi, width, height, params):
    border_thresh = (height + width) / 2 * params['border_thresh_perc']
    logging.debug('border_thresh: %f' % border_thresh)
    return min (roi[0], roi[1], height+1 - roi[2], width+1 - roi[3]) < border_thresh


def sizeProbability (roi, params):
    # naive definition of size
    size = ((roi[2] - roi[0]) + (roi[3] - roi[1])) / 2
    bc = bottomCenter(roi)
    max_prob = params['size_map'][bc[0], bc[1]]
    prob = utilities.gammaProb (size, max_prob, params['size_acceptance'])
    if size < params['min_width']: prob = 0
    logging.debug ('probability of ROI size: %f' % prob)
    return prob


def ratioProbability (roi, params):
    ratio = float(roi[2] - roi[0]) / (roi[3] - roi[1])   # height / width
    prob = utilities.gammaProb (ratio, params['target_ratio'], params['ratio_acceptance'])
    logging.debug ('ratio of roi probability: ' + str(prob))
    return prob



def __filterBorderCar__ (c, car_entry, params):

    carid = carField(car_entry, 'id')
    roi = bbox2roi (carField(car_entry, 'bbox'))
    imagefile = carField(car_entry, 'imagefile')

    c.execute('SELECT width,height FROM images WHERE imagefile=?', (imagefile,))
    (width,height) = c.fetchone()

    border_prob = 1
    if helperDb.doesTableExist(c, 'polygons'):
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

    if params['debug']:
        utilities.drawScoredRoi (params['display'], roi, '', score)



def __filterRatioCar__ (c, car_entry, params):

    carid = carField(car_entry, 'id')
    roi = bbox2roi (carField(car_entry, 'bbox'))
    imagefile = carField(car_entry, 'imagefile')

    # get current score
    c.execute('SELECT name,score FROM cars WHERE id=?', (carid,))
    (name,score) = c.fetchone()
    if score is None: score = 1.0 

    # get probabilities of car, given constraints
    ratio_prob = ratioProbability(roi, params)
    
    # update score in db
    score *= ratio_prob
    c.execute('UPDATE cars SET score=? WHERE id=?', (score,carid))

    if params['debug']:
        utilities.drawScoredRoi (params['display'], roi, '', score)



def __filterSizeCar__ (c, car_entry, params):

    carid = carField(car_entry, 'id')
    roi = bbox2roi (carField(car_entry, 'bbox'))
    imagefile = carField(car_entry, 'imagefile')

    # get current score
    c.execute('SELECT name,score FROM cars WHERE id=?', (carid,))
    (name,score) = c.fetchone()
    if score is None: score = 1.0 

    # get probabilities of car, given constraints
    size_prob = sizeProbability (roi, params)
    
    # update score in db
    score *= size_prob
    c.execute('UPDATE cars SET score=? WHERE id=?', (score,carid))

    if params['debug']:
        utilities.drawScoredRoi (params['display'], roi, '', score)



def __expandCarBbox__ (c, car_entry, params):

    expand_perc = params['expand_perc']
    target_ratio = params['target_ratio']
    carid = carField(car_entry, 'id')
    roi = bbox2roi (carField(car_entry, 'bbox'))
    imagefile = carField(car_entry, 'imagefile')

    c.execute('SELECT height, width FROM images WHERE imagefile=?', (imagefile,))
    (height, width) = c.fetchone()

    old = list(roi)
    if params['keep_ratio']:
        roi = expandRoiToRatio (roi, (height, width), expand_perc, target_ratio)
    else:
        roi = expandRoiFloat (roi, (height, width), (expand_perc, expand_perc))

    # draw roi on the 'display' image
    if params['debug']:
        display = params['image_processor'].imread(imagefile)
        drawRoi (display, old, '', (0,0,255))
        drawRoi (display, roi, '', (255,0,0))
        cv2.imshow('debug', display)
        if params['key_reader'].readKey() == 27:
            cv2.destroyWindow('debug')
            params['debug'] = False

    s = 'x1=?, y1=?, width=?, height=?'
    c.execute('UPDATE cars SET %s WHERE id=?' % s, tuple(roi2bbox(roi) + [carid]))



def __clusterBboxes__ (c, imagefile, params):

    # TODO: now assigned 'vehicle' to all names, angles and color are reset to null

    c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
    car_entries = c.fetchall()
    logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

    # collect rois
    rois = []
    scores = []
    for car_entry in car_entries:
        carid = carField(car_entry, 'id')
        roi = bbox2roi (carField(car_entry, 'bbox'))
        score = carField(car_entry, 'score')
        rois.append (roi)
        scores.append (score)

    # cluster rois
    #params['scores'] = scores
    values = utilities.hierarchicalClusterRoi (rois, params)
    (rois_clustered, clusters, scores1) = values

    # draw roi on the 'display' image
    if params['debug']:
        display = params['image_processor'].imread(imagefile)
        for roi in rois:           drawRoi (display, roi, '', (0,0,255))
        for roi in rois_clustered: drawRoi (display, roi, '', (255,0,0))
        cv2.imshow('debug', display)
        if params['key_reader'].readKey() == 27:
            cv2.destroyWindow('debug')
            params['debug'] = False

    # update db
    for car_entry in car_entries:
        deleteCar (c, carField(car_entry, 'id'))
    for i in range(len(rois_clustered)):
        roi = rois_clustered[i]
        score = scores[i]
        bbox = roi2bbox(roi)
        entry = (imagefile, 'vehicle', bbox[0], bbox[1], bbox[2], bbox[3], score)
        c.execute('''INSERT INTO cars(imagefile,name,x1,y1,width,height,score) 
                     VALUES (?,?,?,?,?,?,?);''', entry)





def filterByBorder (c, params = {}):
    '''
    Zero 'score' of bboxes that is closer than 'min_width' from the border
    '''
    logging.info ('==== filterByBorder ====')
    helperSetup.setParamUnlessThere (params, 'border_thresh_perc', 0.03)
    helperSetup.setParamUnlessThere (params, 'debug',              False)
    helperSetup.setParamUnlessThere (params, 'constraint',         '1')
    helperSetup.setParamUnlessThere (params, 'image_processor', helperImg.ReaderVideo())
    helperSetup.setParamUnlessThere (params, 'key_reader', helperKeys.KeyReaderUser())

    c.execute('SELECT imagefile FROM images')
    image_entries = c.fetchall()

    for (imagefile,) in image_entries:

        if params['debug'] and ('key' not in locals() or key != 27):
            params['display'] = params['image_processor'].imread(imagefile)

        c.execute('SELECT * FROM cars WHERE imagefile=? AND (%s)' % params['constraint'], (imagefile,))
        car_entries = c.fetchall()
        logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

        for car_entry in car_entries:
            __filterBorderCar__ (c, car_entry, params)

        if params['debug'] and ('key' not in locals() or key != 27):
            cv2.imshow('debug', params['display'])
            key = params['key_reader'].readKey()
            if key == 27: cv2.destroyWindow('debug')



def filterByRatio (c, params = {}):
    '''
    Reduce score of boxes, for which height/width is too different than 'target_ratio'
    Score reduction factor is controlled with 'ratio_acceptance'
    '''
    logging.info ('==== filterByRatio ====')
    helperSetup.setParamUnlessThere (params, 'target_ratio',     0.75)
    helperSetup.setParamUnlessThere (params, 'ratio_acceptance', 3)
    helperSetup.setParamUnlessThere (params, 'debug',            False)
    helperSetup.setParamUnlessThere (params, 'constraint',       '1')
    helperSetup.setParamUnlessThere (params, 'image_processor', helperImg.ReaderVideo())
    helperSetup.setParamUnlessThere (params, 'key_reader', helperKeys.KeyReaderUser())

    c.execute('SELECT imagefile FROM images')
    image_entries = c.fetchall()

    for (imagefile,) in image_entries:

        if params['debug'] and ('key' not in locals() or key != 27):
            params['display'] = params['image_processor'].imread(imagefile)

        c.execute('SELECT * FROM cars WHERE imagefile=? AND (%s)' % params['constraint'], (imagefile,))
        car_entries = c.fetchall()
        logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

        for car_entry in car_entries:
            __filterRatioCar__ (c, car_entry, params)

        if params['debug'] and ('key' not in locals() or key != 27):
            cv2.imshow('debug', params['display'])
            key = params['key_reader'].readKey()
            if key == 27: cv2.destroyWindow('debug')



def filterBySize (c, params = {}):
    '''
    Reduce score of boxes, whose size is too different than predicted by 'size_map'
    Score reduction factor is controlled with 'size_acceptance'
    '''
    logging.info ('==== filterBySize ====')
    helperSetup.setParamUnlessThere (params, 'min_width',       10)
    helperSetup.setParamUnlessThere (params, 'size_acceptance', 3)
    helperSetup.setParamUnlessThere (params, 'sizemap_dilate',  21)
    helperSetup.setParamUnlessThere (params, 'debug',           False)
    helperSetup.setParamUnlessThere (params, 'debug_sizemap',   False)
    helperSetup.setParamUnlessThere (params, 'constraint',      '1')
    helperSetup.assertParamIsThere  (params, 'size_map_path')
    helperSetup.setParamUnlessThere (params, 'relpath',         os.getenv('CITY_DATA_PATH'))
    helperSetup.setParamUnlessThere (params, 'image_processor', helperImg.ReaderVideo())
    helperSetup.setParamUnlessThere (params, 'key_reader',      helperKeys.KeyReaderUser())

    # load size_map
    size_map_path = op.join(params['relpath'], params['size_map_path'])
    params['size_map'] = cv2.imread (params['size_map_path'], 0).astype(np.float32)

    if params['debug_sizemap']:
        cv2.imshow ('filterBySize: size_map original', params['size_map'])

    # dilate size_map
    kernel = np.ones ((params['sizemap_dilate'], params['sizemap_dilate']), 'uint8')
    params['size_map'] = cv2.dilate (params['size_map'], kernel)

    if params['debug_sizemap']:
        cv2.imshow ('filterBySize: size_map dilated', params['size_map'])
        cv2.waitKey(-1)

    c.execute('SELECT imagefile FROM images')
    image_entries = c.fetchall()

    for (imagefile,) in image_entries:

        if params['debug'] and ('key' not in locals() or key != 27):
            params['display'] = params['image_processor'].imread(imagefile)

        c.execute('SELECT * FROM cars WHERE imagefile=? AND (%s)' % params['constraint'], (imagefile,))
        car_entries = c.fetchall()
        logging.info ('%d cars found for %s' % (len(car_entries), imagefile))

        for car_entry in car_entries:
            __filterSizeCar__ (c, car_entry, params)

        if params['debug'] and ('key' not in locals() or key != 27):
            cv2.imshow('debug', params['display'])
            key = params['key_reader'].readKey()
            if key == 27: cv2.destroyWindow('debug')



def thresholdScore (c, params = {}):
    '''
    Delete all cars that have score less than 'score_threshold'
    '''
    logging.info ('==== thresholdScore ====')
    helperSetup.setParamUnlessThere (params, 'score_threshold', 0.5)

    c.execute('SELECT id,score FROM cars')
    car_entries = c.fetchall()

    for (carid,score) in car_entries:
        if score < params['score_threshold']:
            c.execute('DELETE FROM cars WHERE id = ?', (carid,))



def expandBboxes (c, params = {}):
    '''
    Expand bbox in every direction.
    If 'keep_ratio' flag is set, the smaller of width and height will be expanded more
    TODO: bbox is clipped to the border if necessary. Maybe think of better ways for border
    '''
    logging.info ('==== expandBboxes ====')
    helperSetup.setParamUnlessThere (params, 'expand_perc', 0.1)
    helperSetup.setParamUnlessThere (params, 'target_ratio', 0.75)  # h / w
    helperSetup.setParamUnlessThere (params, 'keep_ratio', True)
    helperSetup.setParamUnlessThere (params, 'debug', False)
    helperSetup.setParamUnlessThere (params, 'image_processor', helperImg.ReaderVideo())
    helperSetup.setParamUnlessThere (params, 'key_reader', helperKeys.KeyReaderUser())

    c.execute('SELECT imagefile FROM images')
    image_entries = c.fetchall()

    for (imagefile,) in image_entries:

        if params['debug'] and ('key' not in locals() or key != 27):
            params['display'] = params['image_processor'].imread(imagefile)

        c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
        car_entries = c.fetchall()
        logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

        for car_entry in car_entries:
            __expandCarBbox__ (c, car_entry, params)

        if params['debug'] and ('key' not in locals() or key != 27):
            cv2.imshow('debug', params['display'])
            key = params['key_reader'].readKey()
            if key == 27: cv2.destroyWindow('debug')



def clusterBboxes (c, params = {}):
    '''
    Combine close bboxes into one, based on intersection/union ratio via hierarchical clustering
    TODO: implement score-weighted clustering
    '''
    logging.info ('==== clusterBboxes ====')
    helperSetup.setParamUnlessThere (params, 'cluster_threshold', 0.2)
    helperSetup.setParamUnlessThere (params, 'debug',             False)
    helperSetup.setParamUnlessThere (params, 'image_processor', helperImg.ReaderVideo())

    c.execute('SELECT imagefile FROM images')
    image_entries = c.fetchall()

    for (imagefile,) in image_entries:
        __clusterBboxes__ (c, imagefile, params)



def assignOrientations (c, params):
    '''
    assign 'yaw' and 'pitch' angles to each car based on provided yaw and pitch maps 
    '''
    logging.info ('==== assignOrientations ====')
    helperSetup.setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
    helperSetup.assertParamIsThere  (params, 'size_map_path')
    helperSetup.assertParamIsThere  (params, 'pitch_map_path')
    helperSetup.assertParamIsThere  (params, 'yaw_map_path')

    params['size_map_path']  = op.join(params['relpath'], params['size_map_path'])
    params['pitch_map_path'] = op.join(params['relpath'], params['pitch_map_path'])
    params['yaw_map_path']   = op.join(params['relpath'], params['yaw_map_path'])
    if not op.exists(params['size_map_path']):
        raise Exception ('size_map_path does not exist: ' + params['size_map_path'])
    if not op.exists(params['pitch_map_path']):
        raise Exception ('pitch_map_path does not exist: ' + params['pitch_map_path'])
    if not op.exists(params['yaw_map_path']):
        raise Exception ('yaw_map_path does not exist: ' + params['yaw_map_path'])
    size_map  = cv2.imread (params['size_map_path'], 0).astype(np.float32)
    pitch_map = cv2.imread (params['pitch_map_path'], 0).astype(np.float32)
    yaw_map   = cv2.imread (params['yaw_map_path'], -1).astype(np.float32)
    # in the tiff angles belong to [0, 360). Change that to [-180, 180)
    yaw_map   = np.add(-180, np.mod( np.add(180, yaw_map), 360 ) )

    c.execute('SELECT * FROM cars')
    car_entries = c.fetchall()

    for car_entry in car_entries:
        carid = carField (car_entry, 'id')
        roi = bbox2roi (carField (car_entry, 'bbox'))
        bc = bottomCenter(roi)
        if size_map[bc[0], bc[1]] > 0:
            yaw   = float(yaw_map   [bc[0], bc[1]])
            pitch = float(pitch_map [bc[0], bc[1]])
            c.execute('UPDATE cars SET yaw=?, pitch=? WHERE id=?', (yaw, pitch, carid))


# to be removed
def moveDir (c, params):
    logging.info ('==== moveDir ====')

    if 'images_dir' in params:

        c.execute('SELECT imagefile FROM images')
        imagefiles = c.fetchall()

        for (oldfile,) in imagefiles:
            # op.basename (op.dirname(oldfile)), 
            newfile = op.join (params['images_dir'], op.basename (oldfile))
            c.execute('UPDATE images SET imagefile=? WHERE imagefile=?', (newfile, oldfile))
            c.execute('UPDATE cars SET imagefile=? WHERE imagefile=?', (newfile, oldfile))

    if 'masks_dir' in params:

        c.execute('SELECT maskfile FROM images')
        maskfiles = c.fetchall()

        for (oldfile,) in maskfiles:
            # op.basename (op.dirname(oldfile)), 
            newfile = op.join (params['masks_dir'], op.basename (oldfile))
            c.execute('UPDATE images SET maskfile=? WHERE maskfile=?', (newfile, oldfile))


    
def merge (c, cursor_add, params = {}):
    '''
    Merge images and cars (TODO: matches) from 'cursor_add' to current database
    '''
    logging.info ('==== merge ====')

    # copy images
    cursor_add.execute('SELECT * FROM images')
    image_entries = cursor_add.fetchall()

    for image_entry in image_entries:
        imagefile = image_entry[0]
        # check that doesn't exist
        c.execute('SELECT count(*) FROM images WHERE imagefile=?', (imagefile,))
        (num,) = c.fetchone()
        if num > 0:
            logging.warning ('duplicate image found ' + imagefile) 
            continue
        # insert image
        logging.info ('merge: insert imagefile: %s' % (imagefile,))
        c.execute('INSERT INTO images VALUES (?,?,?,?,?,?);', image_entry)
    
    # copy cars
    cursor_add.execute('SELECT * FROM cars')
    car_entries = cursor_add.fetchall()

    for car_entry in car_entries:
        carid = carField (car_entry, 'id')
        s = 'cars(imagefile,name,x1,y1,width,height,score,yaw,pitch,color)'
        c.execute('INSERT INTO ' + s + ' VALUES (?,?,?,?,?,?,?,?,?,?);', car_entry[1:])



# not supported because not used at the moment
def maskScores (c, params = {}):
    '''
    Apply a map (0-255) that will reduce the scores of each car accordingly (255 -> keep same)
    '''
    logging.info ('==== maskScores ====')
    helperSetup.assertParamIsThere (params, 'score_map_path')

    # load the map of scores and normalize it by 1/255
    score_map_path = op.join(os.getenv('CITY_DATA_PATH'), params['score_map_path'])
    if not op.exists(score_map_path):
        raise Exception ('score_map_path does not exist: ' + score_map_path)
    score_map = cv2.imread(score_map_path, -1).astype(float);
    score_map /= 255.0

    c.execute('SELECT * FROM cars')
    car_entries = c.fetchall()

    for car_entry in car_entries:
        carid = carField (car_entry, 'id')
        bbox  = carField (car_entry, 'bbox')
        score = carField (car_entry, 'score')
        if not score: score = 1 

        center = bottomCenter(bbox2roi(bbox))
        score *= score_map[center[0], center[1]]
        c.execute('UPDATE cars SET score=? WHERE id=?', (score, carid))



# need a unit test
def polygonsToMasks (c, params = {}):
    '''
    Transform polygon db table into bboxes when processing results from labelme
    '''
    logging.info ('==== polygonsToMasks ====')

    c.execute('SELECT * FROM images')
    image_entries = c.fetchall()

    imagefile = imageField (image_entries[0], 'imagefile')
    folder = op.basename(op.dirname(imagefile))
    labelme_dir = op.dirname(op.dirname(op.dirname(imagefile)))
    maskdir = op.join(os.getenv('CITY_DATA_PATH'), labelme_dir, 'Masks', folder)
    if op.exists (maskdir): 
        shutil.rmtree (maskdir) 
    os.mkdir (maskdir)

    # copy images and possibly masks
    for image_entry in image_entries:

        imagefile = imageField (image_entry, 'imagefile')
        imagename = op.basename(imagefile)
        maskname = op.splitext(imagename)[0] + '.png'
        folder = op.basename(op.dirname(imagefile))
        labelme_dir = op.dirname(op.dirname(op.dirname(imagefile)))
        maskfile = op.join(labelme_dir, 'Masks', folder, maskname)

        c.execute('UPDATE images SET maskfile=? WHERE imagefile=?', (maskfile, imagefile))

        height = imageField (image_entry, 'height')
        width = imageField (image_entry, 'width')
        mask = np.zeros((height, width), dtype=np.uint8)

        c.execute('SELECT id FROM cars WHERE imagefile=?', (imagefile,))
        for (carid,) in c.fetchall():
            c.execute('SELECT x,y FROM polygons WHERE carid = ?', (carid,))
            polygon_entries = c.fetchall()
            pts = [[pt[0], pt[1]] for pt in polygon_entries]
            cv2.fillConvexPoly(mask, np.asarray(pts, dtype=np.int32), 255)
    
        logging.info ('saving mask to file: ' + maskfile)
        cv2.imwrite (op.join(os.getenv('CITY_DATA_PATH'), maskfile), mask)


def decrementNumbering (c, params = {}):
    helperSetup.setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))

    c.execute('SELECT imagefile,maskfile FROM images')
    for (old_imagefile, old_maskfile) in c.fetchall():
        old_imagepath = op.join(params['relpath'], old_imagefile)
        old_maskpath  = op.join(params['relpath'], old_maskfile)

        old_imagename = op.basename(old_imagefile)
        old_imagenun = int(filter(lambda x: x.isdigit(), old_imagename))
        new_imagename = '%06d.jpg' % (old_imagenun - 1)
        new_imagefile = op.join(op.dirname(old_imagefile), new_imagename)

        old_maskname = op.basename(old_maskfile)
        old_masknun = int(filter(lambda x: x.isdigit(), old_maskname))
        new_maskname = '%06d.jpg' % (old_masknun - 1)
        new_maskfile = op.join(op.dirname(old_maskfile), new_maskname)

        c.execute('UPDATE images SET maskfile=?  WHERE imagefile=?', (new_maskfile,  old_imagefile))
        c.execute('UPDATE images SET imagefile=? WHERE imagefile=?', (new_imagefile, old_imagefile))
        c.execute('UPDATE cars   SET imagefile=? WHERE imagefile=?', (new_imagefile, old_imagefile))
