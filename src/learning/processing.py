import numpy as np
import cv2
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
import setupHelper


def __loadKeys__ (params):
    if 'keys_config' in params.keys() and 'calibrate' not in params.keys(): 
        keys_config = params['keys_config']
    else:
        keys_config = setupHelper.getCalibration()
    logging.info ('left:  ' + str(keys_config['left']))
    logging.info ('right: ' + str(keys_config['right']))
    logging.info ('del:   ' + str(keys_config['del']))
    return keys_config


def isPolygonAtBorder (xs, ys, width, height, params):
    border_thresh = (height + width) / 2 * params['border_thresh_perc']
    dist_to_border = min (xs, [width - x for x in xs], ys, [height - y for y in ys])
    num_too_close = sum([x < border_thresh for x in dist_to_border])
    return num_too_close >= 2


def isRoiAtBorder (roi, width, height, params):
    border_thresh = (height + width) / 2 * params['border_thresh_perc']
    return min (roi[0], roi[1], height+1 - roi[2], width+1 - roi[3]) < border_thresh


def isWrongSize (roi, params):
    bc = bottomCenter(roi)
    # whatever definition of size
    size = ((roi[2] - roi[0]) + (roi[3] - roi[1])) / 2
    return (params['size_map'][bc[0], bc[1]] * params['size_acceptance'][0] > size or
            params['size_map'][bc[0], bc[1]] * params['size_acceptance'][1] < size)


def isBadRatio (roi, params):
    ratio = float(roi[2] - roi[0]) / (roi[3] - roi[1])   # height / width
    return ratio < params['ratio_acceptance'][0] or ratio > params['ratio_acceptance'][1]



def __filterCar__ (cursor, car_entry, params):

    carid = queryField(car_entry, 'id')
    roi = bbox2roi (queryField(car_entry, 'bbox'))
    imagefile = queryField(car_entry, 'imagefile')
    offsetx   = queryField(car_entry, 'offsetx')
    offsety   = queryField(car_entry, 'offsety')

    # prefer to duplicate query rather than pass parameters to function
    cursor.execute('SELECT width,height FROM images WHERE imagefile=?', (imagefile,))
    (width,height) = cursor.fetchone()

    flag = ''
    if checkTableExists(cursor, 'polygons'):
        # get polygon
        cursor.execute('SELECT x,y FROM polygons WHERE carid=?', (carid,))
        polygon_entries = cursor.fetchall()
        xs = [polygon_entry[0] for polygon_entry in polygon_entries]
        ys = [polygon_entry[1] for polygon_entry in polygon_entries]
        assert (len(xs) > 2 and min(xs) != max(xs) and min(ys) != max(ys))
        # filter border
        if isPolygonAtBorder(xs, ys, width, height, params): 
            logging.info ('border polygon ' + str(xs) + ', ' + str(ys))
            flag = 'border'
    else:
        # filter border
        if isRoiAtBorder(roi, width, height, params): 
            logging.info ('border polygon ' + str(roi))
            flag = 'border'

    if isWrongSize(roi, params):
        logging.info ('wrong size of car in ' + str(roi))
        flag = 'badroi'
    if isBadRatio(roi, params):
        logging.info ('bad ratio of roi ' + str(roi))
        flag = 'badroi'
    if roi[3]-roi[1] < params['min_width_thresh']:
        logging.info ('too small ' + str(roi))
        flag = 'badroi'

    if params['debug_show']:
        drawRoi (params['img_show'], roi, (offsety, offsetx), flag)

    if flag != '':
        deleteCar (cursor, carid)



def dbFilter (db_in_path, db_out_path, params):

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    db_in_path   = op.join(CITY_DATA_PATH, db_in_path)
    db_out_path  = op.join(CITY_DATA_PATH, db_out_path)

    setupHelper.setupLogHeader (db_in_path, db_out_path, params, 'dbFilter')
    setupHelper.setupCopyDb (db_in_path, db_out_path)

    params = setupHelper.setParamUnlessThere (params, 'border_thresh_perc', 0.03)
    params = setupHelper.setParamUnlessThere (params, 'min_width_thresh',   10)
    params = setupHelper.setParamUnlessThere (params, 'size_acceptance',   (0.4, 2))
    params = setupHelper.setParamUnlessThere (params, 'ratio_acceptance',  (0.4, 1.5))
    params = setupHelper.setParamUnlessThere (params, 'sizemap_dilate',     21)
    params = setupHelper.setParamUnlessThere (params, 'debug_show',         False)
    params = setupHelper.setParamUnlessThere (params, 'debug_sizemap',      False)
    params = setupHelper.setParamUnlessThere (params, 'car_constraint',      '')


    if 'geom_maps_template' in params.keys():
        size_map_path = params['geom_maps_template'] + 'sizeMap.tiff'
        size_map_path  = op.join(CITY_DATA_PATH, size_map_path)
        logging.info ('will load size_map from: ' + size_map_path)
        params['size_map'] = cv2.imread (size_map_path, 0).astype(np.float32)
    else:
        raise Exception ('geom_maps_template is not given in params')

    if params['debug_sizemap']:
        cv2.imshow ('size_map original', params['size_map'])

    # dilate size_map
    kernel = np.ones ((params['sizemap_dilate'], params['sizemap_dilate']), 'uint8')
    params['size_map'] = cv2.dilate (params['size_map'], kernel)

    if params['debug_sizemap']:
        cv2.imshow ('size_map dilated', params['size_map'])
        cv2.waitKey(-1)

    conn = sqlite3.connect (db_out_path)
    cursor = conn.cursor()

    cursor.execute('SELECT imagefile FROM images')
    image_entries = cursor.fetchall()

    button = 0
    for (imagefile,) in image_entries:

        imagepath = op.join (os.getenv('CITY_DATA_PATH'), imagefile)
        if not op.exists (imagepath):
            raise Exception ('image does not exist: ' + imagepath)
        params['img_show'] = cv2.imread(imagepath) if params['debug_show'] else None

        if 'car_constraint' in params.keys(): 
            car_constraint = params['car_constraint']
        else:
            car_constraint = ''

        cursor.execute('SELECT * FROM cars WHERE imagefile=? ' + car_constraint, (imagefile,))
        car_entries = cursor.fetchall()
        logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

        for car_entry in car_entries:
            __filterCar__ (cursor, car_entry, params)

        if params['debug_show'] and button != 27: 
            cv2.imshow('debug_show', params['img_show'])
            button = cv2.waitKey(-1)
            if button == 27: cv2.destroyWindow('debug_show')

        sys.stdout.flush()

    conn.commit()
    conn.close()



def __expandCarBbox__ (cursor, car_entry, params):

    expand_perc = params['expand_perc']
    target_ratio = params['target_ratio']
    carid = queryField(car_entry, 'id')
    roi = bbox2roi (queryField(car_entry, 'bbox'))
    imagefile = queryField(car_entry, 'imagefile')
    offsetx   = queryField(car_entry, 'offsetx')
    offsety   = queryField(car_entry, 'offsety')

    cursor.execute('SELECT height, width FROM images WHERE imagefile=?', (imagefile,))
    (height, width) = cursor.fetchone()

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
        drawRoi (img_show, old, (offsety, offsetx), '', (0,0,255))
        drawRoi (img_show, roi, (offsety, offsetx), '', (255,0,0))
        cv2.imshow('debug_show', img_show)
        if cv2.waitKey(-1) == 27: 
            cv2.destroyWindow('debug_show')
            params['debug_show'] = False

    cursor.execute('''UPDATE cars SET x1=?, y1=?, width=?, height=? 
                      WHERE id=?''', tuple (roi2bbox(roi) + [carid]))



def dbExpandBboxes (db_in_path, db_out_path, params):

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    db_in_path   = op.join(CITY_DATA_PATH, db_in_path)
    db_out_path  = op.join(CITY_DATA_PATH, db_out_path)

    setupHelper.setupLogHeader (db_in_path, db_out_path, params, 'dbExpandBboxes')
    setupHelper.setupCopyDb (db_in_path, db_out_path)

    params = setupHelper.setParamUnlessThere (params, 'expand_perc', 0.1)
    params = setupHelper.setParamUnlessThere (params, 'target_ratio', 0.75)   # height / width
    params = setupHelper.setParamUnlessThere (params, 'keep_ratio', False)
    params = setupHelper.setParamUnlessThere (params, 'debug_show', False)

    conn = sqlite3.connect (db_out_path)
    cursor = conn.cursor()

    cursor.execute('SELECT imagefile FROM images')
    image_entries = cursor.fetchall()

    for (imagefile,) in image_entries:

        cursor.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
        car_entries = cursor.fetchall()
        logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

        for car_entry in car_entries:
            __expandCarBbox__ (cursor, car_entry, params)

        sys.stdout.flush()

    conn.commit()
    conn.close()



def __clusterBboxes__ (cursor, imagefile, params):

    # TODO: now only works with 0 offsets,
    #       assigned 'vehicle' to all names, angles and color are reset to null

    cursor.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
    car_entries = cursor.fetchall()
    logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

    # collect rois
    rois = []
    for car_entry in car_entries:
        carid = queryField(car_entry, 'id')
        offsetx   = queryField(car_entry, 'offsetx')
        offsety   = queryField(car_entry, 'offsety')
        assert (offsetx == 0 and offsety == 0)
        roi = bbox2roi (queryField(car_entry, 'bbox'))
        rois.append (roi)

    # cluster rois
    rois_clustered = utilities.hierarchicalCluster (rois, params)

    # show
    if params['debug_show']:
        imagepath = op.join (os.getenv('CITY_DATA_PATH'), imagefile)
        if not op.exists (imagepath):
            raise Exception ('image does not exist: ' + imagepath)
        img_show = cv2.imread(imagepath)
        for roi in rois:
            drawRoi (img_show, roi, (0, 0), '', (0,0,255))
        for roi in rois_clustered:
            drawRoi (img_show, roi, (0, 0), '', (255,0,0))
        cv2.imshow('debug_show', img_show)
        if cv2.waitKey(-1) == 27: 
            cv2.destroyWindow('debug_show')
            params['debug_show'] = False

    # update db
    for car_entry in car_entries:
        deleteCar (cursor, queryField(car_entry, 'id'))
    for roi in rois_clustered:
        bbox = roi2bbox(roi)
        entry = (imagefile, 'vehicle', bbox[0], bbox[1], bbox[2], bbox[3], 0, 0)
        cursor.execute('''INSERT INTO cars(imagefile,name,x1,y1,width,height,offsetx,offsety) 
                          VALUES (?,?,?,?,?,?,?,?);''', entry)



def dbClusterBboxes (db_in_path, db_out_path, params = {}):

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    db_in_path   = op.join(CITY_DATA_PATH, db_in_path)
    db_out_path  = op.join(CITY_DATA_PATH, db_out_path)

    setupHelper.setupLogHeader (db_in_path, db_out_path, params, 'dbClusterBboxes')
    setupHelper.setupCopyDb (db_in_path, db_out_path)

    params = setupHelper.setParamUnlessThere (params, 'threshold', 0.2)
    params = setupHelper.setParamUnlessThere (params, 'debug_show', False)
    params = setupHelper.setParamUnlessThere (params, 'debug_clustering', False)

    conn = sqlite3.connect (db_out_path)
    cursor = conn.cursor()

    cursor.execute('SELECT imagefile FROM images')
    image_entries = cursor.fetchall()

    for (imagefile,) in image_entries:
        __clusterBboxes__ (cursor, imagefile, params)

    conn.commit()
    conn.close()



def dbAssignOrientations (db_in_path, db_out_path, params):

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    db_in_path   = op.join(CITY_DATA_PATH, db_in_path)
    db_out_path  = op.join(CITY_DATA_PATH, db_out_path)

    setupHelper.setupLogHeader (db_in_path, db_out_path, params, 'dbAssignOrientations')
    setupHelper.setupCopyDb (db_in_path, db_out_path)

    if not 'geom_maps_dir' in params.keys():
        raise Exception ('geom_maps_dir is not given in params')

    geom_maps_template = params['geom_maps_template']
    pitch_map_path = geom_maps_template + 'pitchMap.tiff'
    pitch_map_path = op.join(CITY_DATA_PATH, pitch_map_path)
    yaw_map_path   = geom_maps_template + 'yawMap.tiff'
    yaw_map_path   = op.join(CITY_DATA_PATH, yaw_map_path)
    pitch_map = cv2.imread (pitch_map_path, 0).astype(np.float32)
    yaw_map   = cv2.imread (yaw_map_path, -1).astype(np.float32)
    yaw_map   = cv2.add (yaw_map, -360)

    conn = sqlite3.connect (db_out_path)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM cars')
    car_entries = cursor.fetchall()

    for car_entry in car_entries:
        carid = queryField (car_entry, 'id')
        roi = bbox2roi (queryField (car_entry, 'bbox'))
        bc = bottomCenter(roi)
        yaw   = float(yaw_map   [bc[0], bc[1]])
        pitch = float(pitch_map [bc[0], bc[1]])
        cursor.execute('UPDATE cars SET yaw=?, pitch=? WHERE id=?', (yaw, pitch, carid))

        sys.stdout.flush()

    conn.commit()
    conn.close()



def dbMove (db_in_path, db_out_path, params):

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    db_in_path   = op.join(CITY_DATA_PATH, db_in_path)
    db_out_path  = op.join(CITY_DATA_PATH, db_out_path)

    setupHelper.setupLogHeader (db_in_path, db_out_path, params, 'dbMove')
    setupHelper.setupCopyDb (db_in_path, db_out_path)

    conn = sqlite3.connect (db_out_path)
    cursor = conn.cursor()

    if 'images_dir' in params.keys():

        cursor.execute('SELECT imagefile FROM images')
        imagefiles = cursor.fetchall()

        for (oldfile,) in imagefiles:
            # op.basename (op.dirname(oldfile)), 
            newfile = op.join (params['images_dir'], op.basename (oldfile))
            cursor.execute('UPDATE images SET imagefile=? WHERE imagefile=?', (newfile, oldfile))
            cursor.execute('UPDATE cars SET imagefile=? WHERE imagefile=?', (newfile, oldfile))

    if 'ghosts_dir' in params.keys():

        cursor.execute('SELECT ghostfile FROM images ')
        ghostfiles = cursor.fetchall()

        for (oldfile,) in ghostfiles:
            # op.basename (op.dirname(oldfile)), 
            newfile = op.join (params['ghosts_dir'], op.basename (oldfile))
            cursor.execute('UPDATE images SET ghostfile=? WHERE ghostfile=?', (newfile, oldfile))

    if 'masks_dir' in params.keys():

        cursor.execute('SELECT maskfile FROM images')
        maskfiles = cursor.fetchall()

        for (oldfile,) in maskfiles:
            # op.basename (op.dirname(oldfile)), 
            newfile = op.join (params['masks_dir'], op.basename (oldfile))
            cursor.execute('UPDATE images SET maskfile=? WHERE maskfile=?', (newfile, oldfile))


    conn.commit()
    conn.close()

        

def dbMerge (db_in_paths, db_out_path, params = {}):

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    db_out_path  = op.join(CITY_DATA_PATH, db_out_path)

    if len(db_in_paths) <= 1:
        raise Exception ('db_in_paths must be a list of at least two elements')
    
    setupHelper.setupLogHeader (db_in_paths[0], db_out_path, params, 'dbMerge')
    setupHelper.setupCopyDb (db_in_paths[0], db_out_path)

    conn_out = sqlite3.connect (db_out_path)
    cursor_out = conn_out.cursor()

    for db_in_path in db_in_paths[1:]:
        db_in_path = op.join(CITY_DATA_PATH, db_in_path)

        conn_in = sqlite3.connect (db_in_path)
        cursor_in = conn_in.cursor()

        cursor_in.execute('SELECT * FROM images')
        image_entries = cursor_in.fetchall()

        # copy images
        for image_entry in image_entries:
            imagefile = image_entry[0]
            # check that doesn't exist
            cursor_out.execute('SELECT count(*) FROM images WHERE imagefile=?', (imagefile,))
            (num,) = cursor_out.fetchone()
            if num > 0:
                logging.warning ('duplicate image ' + imagefile + ' found in ' + db_in_paths[1]) 
                continue
            # insert image
            cursor_out.execute('INSERT INTO images VALUES (?,?,?,?,?,?);', image_entry)
            sys.stdout.flush()
        
        cursor_in.execute('SELECT * FROM cars')
        car_entries = cursor_in.fetchall()

        # copy cars and possible polygons
        for car_entry in car_entries:
            carid = queryField (car_entry, 'id')
            s = 'cars(imagefile,name,x1,y1,width,height,offsetx,offsety,yaw,pitch,color)'
            cursor_out.execute('INSERT INTO ' + s + ' VALUES (?,?,?,?,?,?,?,?,?,?,?);', car_entry[1:])
            carid_new = cursor_out.lastrowid
            if checkTableExists (cursor_in, 'polygons'):
                cursor_in.execute('SELECT * FROM polygons WHERE carid=?', (carid,))
                polygon_entry = cursor_in.fetchone()
                x = polygon_entry[2]
                y = polygon_entry[3]
                cursor_out.execute('INSERT INTO polygons(carid,x,y) VALUES (?,?,?);', (carid_new,x,y))
            sys.stdout.flush()

        conn_in.close()

    conn_out.commit()
    conn_out.close()



def dbExamine (db_in_path, params = {}):

    color_config = {}
    color_config['']       = None
    color_config['black']  = (0,0,0)
    color_config['white']  = (255,255,255)
    color_config['blue']   = (255,0,0)
    color_config['yellow'] = (0,255,255)
    color_config['red']    = (0,0,255)
    color_config['green']  = (0,255,0)
    color_config['gray']   = (128,128,128)
    color_config['badroi'] = color_config['red']

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    db_in_path   = op.join(CITY_DATA_PATH, db_in_path)

    setupHelper.setupLogHeader (db_in_path, '', params, 'dbExamine')

    keys_config = __loadKeys__ (params)

    conn = sqlite3.connect (db_in_path)
    cursor = conn.cursor()

    if 'car_constraint' in params.keys(): 
        car_constraint = ' AND (' + params['car_constraint'] + ')'
    else:
        car_constraint = ''

    cursor.execute('SELECT count(*) FROM cars WHERE 1' + car_constraint)
    (total_num,) = cursor.fetchone()
    logging.info('total number of objects found in db: ' + str(total_num))

    cursor.execute('SELECT imagefile FROM images')
    image_entries = cursor.fetchall()

    if 'imagefile_start' in params.keys(): 
        imagefile_start = params['imagefile_start']
        try:
            index_im = image_entries.index((imagefile_start,))
        except ValueError:
            logging.error ('provided image does not exist ' + imagefile_start)
            sys.exit()
    else:
        index_im = 0

    car_statuses = {}
    button = 0
    index_car = 0
    while button != 27 and index_im < len(image_entries):
        (imagefile,) = image_entries[index_im]

        imagepath = op.join (os.getenv('CITY_DATA_PATH'), imagefile)
        if not op.exists (imagepath):
            raise Exception ('image does not exist: ' + imagepath)
        img = cv2.imread(imagepath)

        cursor.execute('SELECT * FROM cars WHERE imagefile=? ' + car_constraint, (imagefile,))
        car_entries = cursor.fetchall()
        logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

        if index_car == -1: index_car = len(car_entries) - 1  # did 'prev image'
        else: index_car = 0
        while button != 27 and index_car >= 0 and index_car < len(car_entries):
            car_entry = car_entries[index_car]
            carid     = queryField(car_entry, 'id')
            roi       = bbox2roi (queryField(car_entry, 'bbox'))
            imagefile = queryField(car_entry, 'imagefile')
            offsetx   = queryField(car_entry, 'offsetx')
            offsety   = queryField(car_entry, 'offsety')
            name      = queryField(car_entry, 'name')
            color     = queryField(car_entry, 'color')

            img_show = img.copy()
            drawRoi (img_show, roi, (offsety, offsetx), name, color_config[color or ''])

            img_show = cv2.resize(img_show, (0,0), fx=1.5, fy=1.5)
            cv2.imshow('show', img_show)
            button = cv2.waitKey(-1)

            if button == keys_config['left']:
                logging.debug ('prev')
                index_car -= 1
            elif button == keys_config['right']:
                logging.debug ('next')
                index_car += 1

        if button == keys_config['left']:
            logging.debug ('prev image')
            if index_im == 0:
                print ('already the first image')
            else:
                index_im -= 1
                index_car = -1
        else: 
            logging.debug ('next image')
            index_im += 1

    cv2.destroyWindow('show')

    conn.close()



def dbClassifyName (db_in_path, db_out_path, params = {}):

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    db_in_path   = op.join(CITY_DATA_PATH, db_in_path)
    db_out_path  = op.join(CITY_DATA_PATH, db_out_path)

    setupHelper.setupLogHeader (db_in_path, db_out_path, params, 'dbClassifyManually')
    setupHelper.setupCopyDb (db_in_path, db_out_path)

    keys_config = __loadKeys__ (params)

    keys_config[ord('s')] = 'sedan'
    keys_config[ord(' ')] = 'sedan'
    keys_config[ord('d')] = 'double'
    keys_config[ord('h')] = 'vehicle'
    keys_config[ord('t')] = 'taxi'
    keys_config[ord('r')] = 'truck'
    keys_config[ord('v')] = 'van'
    keys_config[ord('m')] = 'minivan'
    keys_config[ord('b')] = 'bus'
    keys_config[ord('p')] = 'pickup'
    keys_config[ord('o')] = 'object'

    conn = sqlite3.connect (db_out_path)
    cursor = conn.cursor()

    if 'car_constraint' in params.keys(): 
        car_constraint = ' AND (' + params['car_constraint'] + ')'
    else:
        car_constraint = ''

    cursor.execute('SELECT imagefile FROM images')
    image_entries = cursor.fetchall()
    if 'imagefile_start' in params.keys(): 
        imagefile_start = params['imagefile_start']
        try:
            index_im = image_entries.index((imagefile_start,))
            logging.info ('starting from image ' + str(index_im))
        except ValueError:
            logging.error ('provided image does not exist ' + imagefile_start)
            sys.exit()
    else:
        index_im = 0

    cursor.execute('SELECT imagefile, ghostfile FROM images')
    image_entries = cursor.fetchall()

    car_statuses = {}
    button = 0
    index_car = 0
    while button != 27 and index_im < len(image_entries):
        (imagefile, ghostfile) = image_entries[index_im]

        ghostpath = op.join (os.getenv('CITY_DATA_PATH'), ghostfile)
        if not op.exists (ghostpath):
            raise Exception ('image does not exist: ' + ghostpath)
        ghost = cv2.imread(ghostpath)

        cursor.execute('SELECT * FROM cars WHERE imagefile=? ' + car_constraint, (imagefile,))
        car_entries = cursor.fetchall()
        logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

        if index_car == -1: index_car = len(car_entries) - 1  # did 'prev image'
        else: index_car = 0
        while button != 27 and index_car >= 0 and index_car < len(car_entries):
            car_entry = car_entries[index_car]
            carid = queryField(car_entry, 'id')
            roi = bbox2roi (queryField(car_entry, 'bbox'))
            imagefile = queryField(car_entry, 'imagefile')
            offsetx   = queryField(car_entry, 'offsetx')
            offsety   = queryField(car_entry, 'offsety')

            # assign label for display
            if carid in car_statuses.keys():
                label = car_statuses[carid]
            else:
                label = queryField(car_entry, 'name')
            logging.debug ('label: "' + (label or '') + '"')

            img_show = ghost.copy()
            drawRoi (img_show, roi, (offsety, offsetx), label)

            img_show = cv2.resize(img_show, (0,0), fx=1.5, fy=1.5)
            cv2.imshow('show', img_show)
            button = cv2.waitKey(-1)

            if button == keys_config['left']:
                logging.debug ('prev')
                index_car -= 1
            elif button == keys_config['right']:
                logging.debug ('next')
                index_car += 1
            elif button == keys_config['del']:
                logging.info ('delete')
                car_statuses[carid] = 'badroi'
                index_car += 1
            elif button in keys_config.keys():
                logging.info (keys_config[button])
                car_statuses[carid] = keys_config[button]
                index_car += 1

        if button == keys_config['left']:
            logging.debug ('prev image')
            if index_im == 0:
                print ('already the first image')
            else:
                index_im -= 1
                index_car = -1
        else: 
            logging.debug ('next image')
            index_im += 1

    cv2.destroyWindow('debug_show')

    # actually delete or update
    for (carid, status) in car_statuses.iteritems():
        if status == 'badroi':
            deleteCar (cursor, carid)
        elif status == '':
            cursor  # nothing
        else:
            cursor.execute('UPDATE cars SET name=? WHERE id=?', (status, carid))

    conn.commit()
    conn.close()



def dbClassifyColor (db_in_path, db_out_path, params = {}):

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    db_in_path   = op.join(CITY_DATA_PATH, db_in_path)
    db_out_path  = op.join(CITY_DATA_PATH, db_out_path)

    setupHelper.setupLogHeader (db_in_path, db_out_path, params, 'dbClassifyManually')
    setupHelper.setupCopyDb (db_in_path, db_out_path)

    keys_config = __loadKeys__ (params)

    keys_config[ord(' ')] = ''
    keys_config[ord('k')] = 'black'
    keys_config[ord('w')] = 'white'
    keys_config[ord('b')] = 'blue'
    keys_config[ord('y')] = 'yellow'
    keys_config[ord('r')] = 'red'
    keys_config[ord('g')] = 'green'
    keys_config[ord('s')] = 'gray'

    color_config = {}
    color_config['']       = None
    color_config['black']  = (0,0,0)
    color_config['white']  = (255,255,255)
    color_config['blue']   = (255,0,0)
    color_config['yellow'] = (0,255,255)
    color_config['red']    = (0,0,255)
    color_config['green']  = (0,255,0)
    color_config['gray']   = (128,128,128)
    color_config['badroi'] = color_config['red']

    conn = sqlite3.connect (db_out_path)
    cursor = conn.cursor()

    if 'car_constraint' in params.keys(): 
        car_constraint = ' AND (' + params['car_constraint'] + ')'
    else:
        car_constraint = ''

    cursor.execute('SELECT imagefile FROM images')
    image_entries = cursor.fetchall()

    if 'imagefile_start' in params.keys(): 
        imagefile_start = params['imagefile_start']
        try:
            index_im = image_entries.index((imagefile_start,))
            logging.info ('starting from image ' + str(index_im))
        except ValueError:
            logging.error ('provided image does not exist ' + imagefile_start)
            sys.exit()
    else:
        index_im = 0

    car_statuses = {}
    button = 0
    index_car = 0
    while button != 27 and index_im < len(image_entries):
        (imagefile,) = image_entries[index_im]

        imagepath = op.join (os.getenv('CITY_DATA_PATH'), imagefile)
        if not op.exists (imagepath):
            raise Exception ('image does not exist: ' + imagepath)
        img = cv2.imread(imagepath)

        cursor.execute('SELECT * FROM cars WHERE imagefile=? ' + car_constraint, (imagefile,))
        car_entries = cursor.fetchall()
        logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

        if index_car == -1: index_car = len(car_entries) - 1  # did 'prev image'
        else: index_car = 0
        while button != 27 and index_car >= 0 and index_car < len(car_entries):
            car_entry = car_entries[index_car]
            carid     = queryField(car_entry, 'id')
            roi       = bbox2roi (queryField(car_entry, 'bbox'))
            imagefile = queryField(car_entry, 'imagefile')
            offsetx   = queryField(car_entry, 'offsetx')
            offsety   = queryField(car_entry, 'offsety')

            # assign label for display
            if carid in car_statuses.keys():
                label = car_statuses[carid]
            else:
                label = queryField(car_entry, 'color')
            logging.debug ('label: "' + (label or '') + '"')

            img_show = img.copy()
            drawRoi (img_show, roi, (offsety, offsetx), label, color_config[label or ''])

            img_show = cv2.resize(img_show, (0,0), fx=1.5, fy=1.5)
            cv2.imshow('show', img_show)
            button = cv2.waitKey(-1)

            if button == keys_config['left']:
                logging.debug ('prev')
                index_car -= 1
            elif button == keys_config['right']:
                logging.debug ('next')
                index_car += 1
            elif button == keys_config['del']:
                logging.info ('delete')
                car_statuses[carid] = 'badroi'
                index_car += 1
            elif button in keys_config.keys():
                logging.info (keys_config[button])
                car_statuses[carid] = keys_config[button]
                index_car += 1

        if button == keys_config['left']:
            logging.debug ('prev image')
            if index_im == 0:
                print ('already the first image')
            else:
                index_im -= 1
                index_car = -1
        else: 
            logging.debug ('next image')
            index_im += 1

    cv2.destroyWindow('debug_show')

    # actually delete or update
    for (carid, status) in car_statuses.iteritems():
        if status == 'badroi':
            deleteCar (cursor, carid)
        elif status == '':
            cursor.execute('UPDATE cars SET color=? WHERE id=?', (None, carid))
        else:
            cursor.execute('UPDATE cars SET color=? WHERE id=?', (status, carid))

    conn.commit()
    conn.close()




def dbPolygonsToMasks (db_in_path, db_out_path, params = {}):

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    db_in_path   = op.join(CITY_DATA_PATH, db_in_path)
    db_out_path  = op.join(CITY_DATA_PATH, db_out_path)

    setupHelper.setupLogHeader (db_in_path, db_out_path, params, 'dbPolygonsToMasks')
    setupHelper.setupCopyDb (db_in_path, db_out_path)

    conn = sqlite3.connect (db_out_path)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM images')
    image_entries = cursor.fetchall()

    imagefile = getImageField (image_entries[0], 'imagefile')
    folder = op.basename(op.dirname(imagefile))
    labelme_dir = op.dirname(op.dirname(op.dirname(imagefile)))
    maskdir = op.join(os.getenv('CITY_DATA_PATH'), labelme_dir, 'Masks', folder)
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

        cursor.execute('UPDATE images SET maskfile=? WHERE imagefile=?', (maskfile, imagefile))

        height = getImageField (image_entry, 'height')
        width = getImageField (image_entry, 'width')
        mask = np.zeros((height, width), dtype=np.uint8)

        cursor.execute('SELECT id,offsetx,offsety FROM cars WHERE imagefile=?', (imagefile,))
        for (carid,offsetx,offsety) in cursor.fetchall():
            cursor.execute('SELECT x,y FROM polygons WHERE carid = ?', (carid,))
            polygon_entries = cursor.fetchall()
            pts = [[pt[0]+offsetx, pt[1]+offsety] for pt in polygon_entries]
            cv2.fillConvexPoly(mask, np.asarray(pts, dtype=np.int32), 255)
    
        logging.info ('saving mask to file: ' + maskfile)
        cv2.imwrite (op.join(os.getenv('CITY_DATA_PATH'), maskfile), mask)

    conn.commit()
    conn.close()


def dbCustomScript (db_in_path, db_out_path, params = {}):

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()
    db_in_path   = op.join(CITY_DATA_PATH, db_in_path)
    db_out_path  = op.join(CITY_DATA_PATH, db_out_path)

    setupHelper.setupLogHeader (db_in_path, db_out_path, params, 'dbCustomScript')
    setupHelper.setupCopyDb (db_in_path, db_out_path)

    conn = sqlite3.connect (db_out_path)
    cursor = conn.cursor()

    cursor.execute('ALTER TABLE images ADD maskfile TEXT NULL')

    cursor.execute('SELECT * FROM images')
    image_entries = cursor.fetchall()

    for image_entry in image_entries:

        imagefile = getImageField (image_entry, 'imagefile')

        cursor.execute('SELECT maskfile FROM masks WHERE imagefile = ?', (imagefile,))
        (maskfile,) = cursor.fetchone()

        cursor.execute('UPDATE images SET maskfile=? WHERE imagefile=?', (maskfile, imagefile))

    cursor.execute('DROP TABLE masks')

    conn.commit()
    conn.close()

    
