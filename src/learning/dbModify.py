import os, sys, os.path as op
from math import ceil
import numpy as np
import cv2
import logging
import sqlite3
import json
import random
import dbUtilities
from helperDb          import createDb, deleteCar, carField, imageField
from helperDb          import doesTableExist, createTablePolygons
from dbUtilities       import bbox2roi, roi2bbox, bottomCenter, drawRoi
from annotations.terms import TermTree
from helperSetup       import setParamUnlessThere, assertParamIsThere, atcity
from helperKeys        import KeyReaderUser
from helperImg         import ReaderVideo, ProcessorVideo, SimpleWriter


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
    prob = dbUtilities.gammaProb (size, max_prob, params['size_acceptance'])
    if size < params['min_width']: prob = 0
    logging.debug ('probability of ROI size: %f' % prob)
    return prob


def ratioProbability (roi, params):
    ratio = float(roi[2] - roi[0]) / (roi[3] - roi[1])   # height / width
    prob = dbUtilities.gammaProb (ratio, params['target_ratio'], params['ratio_acceptance'])
    logging.debug ('ratio of roi probability: ' + str(prob))
    return prob



def _filterBorderCar_ (c, car_entry, params):

    carid = carField(car_entry, 'id')
    roi = bbox2roi (carField(car_entry, 'bbox'))
    imagefile = carField(car_entry, 'imagefile')

    c.execute('SELECT width,height FROM images WHERE imagefile=?', (imagefile,))
    (width,height) = c.fetchone()

    is_good = 1
    if doesTableExist(c, 'polygons'):
        # get polygon
        c.execute('SELECT x,y FROM polygons WHERE carid=?', (carid,))
        polygon_entries = c.fetchall()
        if not polygon_entries:
            logging.debug ('no polygon for carid %s. Skip' % carid)
        else:
            xs = [polygon_entry[0] for polygon_entry in polygon_entries]
            ys = [polygon_entry[1] for polygon_entry in polygon_entries]
            assert len(xs) > 2 and min(xs) != max(xs) and min(ys) != max(ys), \
                   'xs: %s, ys: %s' % (xs, ys)
            # filter border
            if isPolygonAtBorder(xs, ys, width, height, params): 
                logging.info ('border polygon %s, %s' % (str(xs), str(ys)))
                is_good = 0

    # filter border
    if isRoiAtBorder(roi, width, height, params): 
        logging.info ('border roi %s' % str(roi))
        is_good = 0

    # get current score
    c.execute('SELECT name,score FROM cars WHERE id=?', (carid,))
    (name,score) = c.fetchone()
    if score is None: score = 1.0 

    # update score in db
    score *= is_good
    c.execute('UPDATE cars SET score=? WHERE id=?', (score,carid))

    if params['debug']:
        dbUtilities.drawScoredRoi (params['display'], roi, '', score)



def _filterRatioCar_ (c, car_entry, params):

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
        dbUtilities.drawScoredRoi (params['display'], roi, '', score)



def _filterSizeCar_ (c, car_entry, params):

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
        dbUtilities.drawScoredRoi (params['display'], roi, '', score)



def _expandCarBbox_ (c, car_entry, params):

    expand_perc = params['expand_perc']
    target_ratio = params['target_ratio']
    carid = carField(car_entry, 'id')
    roi = bbox2roi (carField(car_entry, 'bbox'))
    imagefile = carField(car_entry, 'imagefile')

    c.execute('SELECT height, width FROM images WHERE imagefile=?', (imagefile,))
    (height, width) = c.fetchone()

    old = list(roi)
    if params['keep_ratio']:
        roi = dbUtilities.expandRoiToRatio (roi, (height, width), expand_perc, target_ratio)
    else:
        roi = dbUtilities.expandRoiFloat (roi, (height, width), (expand_perc, expand_perc))

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



def _clusterBboxes_ (c, imagefile, params):
    assertParamIsThere (params, 'terms')

    c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
    car_entries = c.fetchall()
    logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

    # collect rois
    rois = []
    names = []
    #scores = []
    for car_entry in car_entries:
        roi = bbox2roi (carField(car_entry, 'bbox'))
        name = carField(car_entry, 'name')
        if name is None: name = 'vehicle'
        #score = carField(car_entry, 'score')
        rois.append (roi)
        names.append (name)
        #scores.append (score)

    # cluster rois
    #params['scores'] = scores
    (rois_clustered, clusters, scores) = dbUtilities.hierarchicalClusterRoi (rois, params)

    names_clustered = []
    for cluster in list(set(clusters)):
        names_in_cluster = [x for i, x in enumerate(names) if clusters[i] == cluster]
        # try to be as specific about the name as possible
        #for i in range(1, len(names_in_cluster)):
        #    common_root = params['terms'].get_common_root(names_in_cluster[i], names_in_cluster[i-1])
        # Start with two clusters
        name = names_in_cluster[0]
        if len(names_in_cluster) > 1:
            common_root = params['terms'].get_common_root(names_in_cluster[0], names_in_cluster[1])
            if names_in_cluster[0] == common_root:
                # names_in_cluster[1] is more specific
                name = names_in_cluster[1]
            elif names_in_cluster[1] == common_root:
                # names_in_cluster[0] is more specific
                name = names_in_cluster[0]
            else:
                # they are not in the same branch
                name = common_root
            # upgrade to the 'known' name
            name = params['terms'].best_match(name)
            logging.info ('chose "%s" from names "%s"' % (name, ','.join(names_in_cluster)))
        names_clustered.append(name)

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
        name = names_clustered[i]
        score = scores[i]
        bbox = roi2bbox(roi)
        entry = (imagefile, name, bbox[0], bbox[1], bbox[2], bbox[3], score)
        c.execute('''INSERT INTO cars(imagefile,name,x1,y1,width,height,score) 
                     VALUES (?,?,?,?,?,?,?);''', entry)





def filterByBorder (c, params = {}):
    '''
    Zero 'score' of bboxes that is closer than 'border_thresh_perc' from border
    '''
    logging.info ('==== filterByBorder ====')
    setParamUnlessThere (params, 'border_thresh_perc', 0.03)
    setParamUnlessThere (params, 'debug',              False)
    setParamUnlessThere (params, 'image_processor',    ReaderVideo())
    setParamUnlessThere (params, 'key_reader',         KeyReaderUser())

    c.execute('SELECT imagefile FROM images')
    image_entries = c.fetchall()

    for (imagefile,) in image_entries:

        if params['debug'] and ('key' not in locals() or key != 27):
            params['display'] = params['image_processor'].imread(imagefile)

        c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
        car_entries = c.fetchall()
        logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

        for car_entry in car_entries:
            _filterBorderCar_ (c, car_entry, params)

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
    setParamUnlessThere (params, 'target_ratio',     0.75)
    setParamUnlessThere (params, 'ratio_acceptance', 3)
    setParamUnlessThere (params, 'debug',            False)
    setParamUnlessThere (params, 'image_processor',  ReaderVideo())
    setParamUnlessThere (params, 'key_reader',       KeyReaderUser())

    c.execute('SELECT imagefile FROM images')
    image_entries = c.fetchall()

    for (imagefile,) in image_entries:

        if params['debug'] and ('key' not in locals() or key != 27):
            params['display'] = params['image_processor'].imread(imagefile)

        c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
        car_entries = c.fetchall()
        logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

        for car_entry in car_entries:
            _filterRatioCar_ (c, car_entry, params)

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
    setParamUnlessThere (params, 'min_width',       10)
    setParamUnlessThere (params, 'size_acceptance', 3)
    setParamUnlessThere (params, 'sizemap_dilate',  21)
    setParamUnlessThere (params, 'debug',           False)
    setParamUnlessThere (params, 'debug_sizemap',   False)
    assertParamIsThere  (params, 'size_map_path')
    setParamUnlessThere (params, 'relpath',         os.getenv('CITY_DATA_PATH'))
    setParamUnlessThere (params, 'image_processor', ReaderVideo())
    setParamUnlessThere (params, 'key_reader',      KeyReaderUser())

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

        c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
        car_entries = c.fetchall()
        logging.info ('%d cars found for %s' % (len(car_entries), imagefile))

        for car_entry in car_entries:
            _filterSizeCar_ (c, car_entry, params)

        if params['debug'] and ('key' not in locals() or key != 27):
            cv2.imshow('debug', params['display'])
            key = params['key_reader'].readKey()
            if key == 27: cv2.destroyWindow('debug')


def filterUnknownNames (c):
    ''' filter away car entries with unknown names '''
    
    # load terms tree
    dictionary_path = op.join(os.getenv('CITY_PATH'), 'src/learning/annotations/dictionary.json')
    json_file = open(dictionary_path);
    terms = TermTree.from_dict(json.load(json_file))
    json_file.close()

    c.execute('SELECT id,name FROM cars')
    for (carid,name) in c.fetchall():
        if terms.best_match(name) == 'object':
            c.execute('DELETE FROM cars WHERE id=?', (carid,))


def filterCustom (c, params = {}):
    '''Apply car_constraint to cars table and filter eveything which does not match 
    '''
    setParamUnlessThere (params, 'image_constraint', '1')
    setParamUnlessThere (params, 'car_constraint', '1')
    c.execute('DELETE FROM images WHERE NOT (%s)' % params['image_constraint'])
    c.execute('''SELECT id FROM cars WHERE 
                 NOT (%s) OR imagefile NOT IN 
                 (SELECT imagefile FROM images WHERE (%s))''' 
                 % (params['car_constraint'], params['image_constraint']))
    car_ids = c.fetchall()
    for (car_id,) in car_ids:
        deleteCar (c, car_id)


def deleteEmptyImages (c, params = {}):
    c.execute('DELETE FROM images WHERE imagefile NOT IN '
              '(SELECT imagefile FROM cars)')


def thresholdScore (c, params = {}):
    '''
    Delete all cars that have score less than 'score_threshold'
    '''
    logging.info ('==== thresholdScore ====')
    setParamUnlessThere (params, 'score_threshold', 0.5)

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
    setParamUnlessThere (params, 'expand_perc', 0.1)
    setParamUnlessThere (params, 'target_ratio', 0.75)  # h / w
    setParamUnlessThere (params, 'keep_ratio', True)
    setParamUnlessThere (params, 'debug', False)
    setParamUnlessThere (params, 'image_processor', ReaderVideo())
    setParamUnlessThere (params, 'key_reader',      KeyReaderUser())

    c.execute('SELECT imagefile FROM images')
    image_entries = c.fetchall()

    for (imagefile,) in image_entries:

        if params['debug'] and ('key' not in locals() or key != 27):
            params['display'] = params['image_processor'].imread(imagefile)

        c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
        car_entries = c.fetchall()
        logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

        for car_entry in car_entries:
            _expandCarBbox_ (c, car_entry, params)

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
    setParamUnlessThere (params, 'cluster_threshold', 0.2)
    setParamUnlessThere (params, 'debug',             False)
    setParamUnlessThere (params, 'key_reader',        KeyReaderUser())
    setParamUnlessThere (params, 'image_processor',   ReaderVideo())

    # load terms tree
    dictionary_path = op.join(os.getenv('CITY_PATH'), 'src/learning/annotations/dictionary.json')
    json_file = open(dictionary_path);
    terms = TermTree.from_dict(json.load(json_file))
    json_file.close()
    params['terms'] = terms

    c.execute('SELECT imagefile FROM images')
    image_entries = c.fetchall()

    for (imagefile,) in image_entries:
        _clusterBboxes_ (c, imagefile, params)



def assignOrientations (c, params):
    '''
    assign 'yaw' and 'pitch' angles to each car based on provided yaw and pitch maps 
    '''
    logging.info ('==== assignOrientations ====')
    setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
    assertParamIsThere  (params, 'size_map_path')
    assertParamIsThere  (params, 'pitch_map_path')
    assertParamIsThere  (params, 'yaw_map_path')

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


    
def merge (c, c_add, params = {}):
    '''
    Merge images and cars (TODO: matches) from 'c_add' to current database
    '''
    logging.info ('==== merge ====')

    # copy images
    c_add.execute('SELECT * FROM images')
    image_entries = c_add.fetchall()

    for image_entry in image_entries:
        imagefile = image_entry[0]
        # check that doesn't exist
        c.execute('SELECT count(*) FROM images WHERE imagefile=?', (imagefile,))
        (num,) = c.fetchone()
        if num > 0:
            logging.warning ('duplicate image found %s' % imagefile) 
            continue
        # insert image
        logging.info ('merge: insert imagefile: %s' % (imagefile,))
        c.execute('INSERT INTO images VALUES (?,?,?,?,?,?)', image_entry)
    
    # copy cars and polygons
    c_add.execute('SELECT * FROM cars')
    car_entries = c_add.fetchall()

    for car_entry in car_entries:

        # insert car
        carid = carField (car_entry, 'id')
        s = 'cars(imagefile,name,x1,y1,width,height,score,yaw,pitch,color)'
        c.execute('INSERT INTO %s VALUES (?,?,?,?,?,?,?,?,?,?)' % s, car_entry[1:])
        new_carid = c.lastrowid

        # insert all its polygons
        if doesTableExist(c_add, 'polygons'):
            if not doesTableExist(c, 'polygons'): 
                createTablePolygons(c)
            c_add.execute('SELECT x,y FROM polygons WHERE carid = ?', (carid,))
            polygon_entries = c_add.fetchall()
            for x,y in polygon_entries:
                s = 'polygons(carid,x,y)'
                c.execute('INSERT INTO %s VALUES (?,?,?)' % s, (new_carid,x,y))



def split (c, db_out_names={'train': 0.5, 'test': 0.5}, randomly=True):
  ''' Split a db into several sets (randomly or sequentially).
  This function violates the principle of receiving cursors, for simplicity.
  Args: out_dir      - relative to CITY_DATA_PATH
        db_out_names - names of output db-s and their percentage;
                       if percentage sums to >1, last db-s will be underfilled.
  '''
  out_dir = os.path.dirname(in_db_file)

  c.execute('SELECT imagefile FROM images')
  imagefiles = sorted(c.fetchall())
  if randomly: random.shuffle(imagefiles)

  current = 0
  for db_out_name,setfraction in db_out_names.iteritems():
    num_images_in_set = int(ceil(len(imagefiles) * setfraction))
    next = min(current + num_images_in_set, len(imagefiles))

    db_out_path = atcity(op.join(out_dir, '%s.db' % db_out_name))
    if op.exists(db_out_path): os.remove(db_out_path)
    conn = sqlite3.connect(db_out_path)
    createDb(conn)
    c_out = conn.cursor()

    for imagefile, in imagefiles[current : next]:

      # copy an entry from image table
      s = 'imagefile,width,height,src,maskfile,time'
      c.execute('SELECT %s FROM images WHERE imagefile=?' % s, (imagefile,))
      c_out.execute('INSERT INTO images(%s) VALUES (?,?,?,?,?,?)' % s, c.fetchone())

      # copy cars for that imagefile (ids are not copied)
      s = 'imagefile,name,x1,y1,width,height,score,yaw,pitch,color'
      c.execute('SELECT %s FROM cars WHERE imagefile=?' % s, (imagefile,))
      for car in c.fetchall():
        c_out.execute('INSERT INTO cars(%s) VALUES (?,?,?,?,?,?,?,?,?,?)' % s, car)

    current = next

    conn.commit()
    conn.close()

  # copying matches is not implemented (how to copy them anyway?)
  c.execute('SELECT COUNT(*) FROM matches')
  if c.fetchone()[0] > 0:
    logging.warning('matches table is not empty, they will not be copied.')



# not supported because not used at the moment
def maskScores (c, params = {}):
    '''
    Apply a map (0-255) that will reduce the scores of each car accordingly (255 -> keep same)
    '''
    logging.info ('==== maskScores ====')
    assertParamIsThere (params, 'score_map_path')

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



# TODO: need a unit test
def polygonsToMasks (c, c_labelled=None, c_all=None, params = {}):
    '''
    Create masks and maskfile db entries from polygons table.
    Currently only supports ProcessorVideo (writes masks to video)
    '''
    logging.info ('==== polygonsToMasks ====')
    setParamUnlessThere (params, 'relpath',    os.getenv('CITY_DATA_PATH'))
    setParamUnlessThere (params, 'mask_name',  'mask-poly.avi')

    # Assume mask field is null. Deduce the out mask name from imagefile.
    #   Also send the image video to processor, so that it deduces video params.
    c_all.execute('SELECT imagefile,width,height FROM images')
    image_entries = c_all.fetchall()
    in_image_video_file = '%s.avi' % op.dirname(image_entries[0][0])
    out_mask_video_file = '%s/%s' % (op.dirname(in_image_video_file), params['mask_name'])
    logging.info ('polygonsToMasks: in_image_video_file: %s' % in_image_video_file)
    logging.info ('polygonsToMasks: out_mask_video_file: %s' % out_mask_video_file)
    processor = ProcessorVideo \
         ({'out_dataset': {in_image_video_file: out_mask_video_file} })

    # copy images and possibly masks
    for i,(imagefile,width,height) in enumerate(image_entries):
      processor.maskread (imagefile)  # processor needs to read first
      
      c_labelled.execute('SELECT COUNT(*) FROM images WHERE imagefile=?', (imagefile,))
      is_unlabelled = (c_labelled.fetchone()[0] == 0)

      if is_unlabelled:
        logging.info ('imagefile NOT labelled: %s: ' % imagefile)
        mask = np.zeros((height, width), dtype=bool)
        maskfile = processor.maskwrite (mask, imagefile)
        c.execute('UPDATE images SET maskfile=NULL WHERE imagefile=?', (imagefile,))

      else:
        logging.info ('imagefile labelled:     %s: ' % imagefile)
        mask = np.zeros((height, width), dtype=np.uint8)
        c_labelled.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
        for car_entry in c_labelled.fetchall():
          carid = carField(car_entry, 'id')
          c_labelled.execute('SELECT x,y FROM polygons WHERE carid = ?', (carid,))
          polygon_entries = c_labelled.fetchall()
          pts = [[pt[0], pt[1]] for pt in polygon_entries]
          cv2.fillConvexPoly(mask, np.asarray(pts, dtype=np.int32), 255)
          # maybe copy car entry
          if c != c_labelled:  # c == c_all
            c.execute('INSERT INTO cars VALUES (?,?,?,?,?,?,?,?,?,?,?)', car_entry)
        mask = mask > 0

        maskfile = processor.maskwrite (mask, imagefile)
        c.execute('UPDATE images SET maskfile=? WHERE imagefile=?', 
          (maskfile, imagefile))


# TODO: need a unit test
def generateBackground (c, out_videofile, params={}):
  ''' Generate background video using mask and update imagefiles in db. '''

  logging.info ('==== polygonsToMasks ====')
  setParamUnlessThere (params, 'relpath',       os.getenv('CITY_DATA_PATH'))
  setParamUnlessThere (params, 'show_debug',    False)
  setParamUnlessThere (params, 'key_reader',    KeyReaderUser())
  setParamUnlessThere (params, 'image_reader',  ReaderVideo())
  setParamUnlessThere (params, 'dilate_radius', 2);
  setParamUnlessThere (params, 'lr',            0.2);

  video_writer = SimpleWriter(vimagefile=out_videofile)

  # structure element for dilation
  rad = params['dilate_radius']
  kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (rad, rad))

  c.execute('SELECT imagefile,maskfile FROM images')
  image_entries = c.fetchall()
  logging.info ('will process %d image entries' % len(image_entries))

  back = None

  for imagefile,maskfile in image_entries:
    img = params['image_reader'].imread(imagefile)
    mask = params['image_reader'].maskread(maskfile)

    if back is None:
      back = img

    mask = cv2.dilate(mask.astype(np.uint8)*255, kernel) > 128
    mask = np.dstack((mask, mask, mask))
    unmasked = np.invert(mask)
    lr = params['lr']
    back[unmasked] = img[unmasked] * lr + back[unmasked] * (1-lr)

    if params['show_debug']:
      cv2.imshow('debug', np.hstack((back, mask.astype(np.uint8)*255)))
      cv2.waitKey(10)
      if params['key_reader'].readKey() == 27:
        cv2.destroyWindow('debug')
        params['show_debug'] = False

    backfile = video_writer.imwrite(back)
    c.execute('UPDATE images SET imagefile=? WHERE imagefile=?', (backfile, imagefile))
    logging.info ('wrote backfile %s' % backfile)

  video_writer.close()
  c.execute('DELETE FROM cars')

