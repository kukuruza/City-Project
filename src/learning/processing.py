#!/bin/python

import numpy as np
import cv2
import os, sys
import collections
import logging
import os.path as op
import glob
import shutil
import sqlite3
from dbInterface import deleteCar, queryField, checkTableExists
import dbInterface
from utilities import bbox2roi, roi2bbox, bottomCenter, getCalibration


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




class Processor:

    border_thresh_perc = 0.03
    expand_perc = 0.1
    target_ratio = 0.75   # height / width
    keep_ratio = False
    size_acceptance = (0.4, 2)
    ratio_acceptance = (0.4, 1.5)
    sizemap_dilate = 21
    debug_show = False
    debug_sizemap = False
    min_width_thresh = 0

    def __init__(self, params):

        logging.info ('=== processing.__init__ ===')
        logging.info ('params: ' + str(params))
        logging.info ('')

        if 'border_thresh_perc' in params.keys(): 
            self.border_thresh_perc = params['border_thresh_perc']
        if 'min_width_thresh' in params.keys(): 
            self.min_width_thresh = params['min_width_thresh']
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
        if 'debug_sizemap' in params.keys(): 
            self.debug_sizemap = params['debug_sizemap']

        if 'geom_maps_dir' in params.keys():
            size_map_path  = op.join (geom_maps_dir, 'sizeMap.tiff')
            self.size_map  = cv2.imread (size_map_path, 0).astype(np.float32)
        else:
            raise Exception ('Processor: geom_maps_dir is not given in params')

        if self.debug_sizemap:
            cv2.imshow ('size_map original', self.size_map)

        # dilate size_map
        kernel = np.ones ((self.sizemap_dilate, self.sizemap_dilate), 'uint8')
        self.size_map = cv2.dilate (self.size_map, kernel)

        if self.debug_sizemap:
            cv2.imshow ('size_map dilated', self.size_map)
            cv2.waitKey(-1)



    def isPolygonAtBorder (self, xs, ys, width, height):
        border_thresh = (height + width) / 2 * self.border_thresh_perc
        dist_to_border = min (xs, [width - x for x in xs], ys, [height - y for y in ys])
        num_too_close = sum([x < border_thresh for x in dist_to_border])
        return num_too_close >= 2


    def isRoiAtBorder (self, roi, width, height):
        border_thresh = (height + width) / 2 * self.border_thresh_perc
        return min (roi[0], roi[1], height+1 - roi[2], width+1 - roi[3]) < border_thresh


    def isWrongSize (self, roi):
        bc = bottomCenter(roi)
        # whatever definition of size
        size = ((roi[2] - roi[0]) + (roi[3] - roi[1])) / 2
        return self.size_map [bc[0], bc[1]] * self.size_acceptance[0] > size or \
               self.size_map [bc[0], bc[1]] * self.size_acceptance[1] < size


    def isBadRatio (self, roi):
        ratio = float(roi[2] - roi[0]) / (roi[3] - roi[1])   # height / width
        return ratio < self.ratio_acceptance[0] or ratio > self.ratio_acceptance[1]


    def debugShowAddRoi (self, img, roi, (offsety, offsetx), flag):
        if self.debug_show: 
            if flag == 'border':
                color = (0,255,255)
            elif flag == 'badroi':
                color = (0,0,255)
            else:
                color = (255,0,0)
            roi[0] += offsety
            roi[1] += offsetx
            roi[2] += offsety
            roi[3] += offsetx
            cv2.rectangle (img, (roi[1], roi[0]), (roi[3], roi[2]), color)


    def processCar (self, car_entry):

        carid = queryField(car_entry, 'id')
        roi = bbox2roi (queryField(car_entry, 'bbox'))
        imagefile = queryField(car_entry, 'imagefile')
        offsetx   = queryField(car_entry, 'offsetx')
        offsety   = queryField(car_entry, 'offsety')

        # prefer to duplicate query rather than pass parameters to function
        self.cursor.execute('SELECT width,height FROM images WHERE imagefile=?', (imagefile,))
        (width,height) = self.cursor.fetchone()

        is_bad = False
        if checkTableExists(self.cursor, 'polygons'):
            # get polygon
            self.cursor.execute('SELECT x,y FROM polygons WHERE carid=?', 
                                (queryField(car_entry, 'id'),))
            polygon_entries = self.cursor.fetchall()
            xs = [polygon_entry[0] for polygon_entry in polygon_entries]
            ys = [polygon_entry[1] for polygon_entry in polygon_entries]
            assert (len(xs) > 2 and min(xs) != max(xs) and min(ys) != max(ys))
            # filter border
            if self.isPolygonAtBorder(xs, ys, width, height): 
                logging.info ('border polygon ' + str(xs) + ', ' + str(ys))
                flag = 'border'
                is_bad = True
        else:
            # filter border
            if self.isRoiAtBorder(roi, width, height): 
                logging.info ('border polygon ' + str(roi))
                flag = 'border'
                is_bad = True


        if self.isWrongSize(roi):
            logging.info ('wrong size of car in ' + str(roi))
            flag = 'badroi'
            is_bad = True
        if self.isBadRatio(roi):
            logging.info ('bad ratio of roi ' + str(roi))
            flag = 'badroi'
            is_bad = True
        if roi[3]-roi[1] < self.min_width_thresh:
            logging.info ('too small ' + str(roi))
            flag = 'badroi'
            is_bad = True

        if is_bad:
            deleteCar (self.cursor, carid)
            self.debugShowAddRoi (self.img_show, roi, (offsety, offsetx), flag)
            return

        # expand bbox
        if self.keep_ratio:
            roi = expandRoiToRatio (roi, (height, width), self.expand_perc, self.target_ratio)
        else:
            roi = expandRoiFloat (roi, (height, width), (self.expand_perc, self.expand_perc))
        self.debugShowAddRoi (self.img_show, roi, (offsety, offsetx), 'good')

        self.cursor.execute('''UPDATE cars SET x1=?, y1=?, width=?, height=? 
                               WHERE id=?''', tuple (roi2bbox(roi) + [carid]))



    def processDb (self, db_in_path, db_out_path):

        logging.info ('=== processing.processDb ===')
        logging.info ('db_in_path: ' + db_in_path)
        logging.info ('db_out_path: ' + db_out_path)
        logging.info ('')

        if not op.exists (db_in_path):
            raise Exception ('db does not exist: ' + db_in_path)

        if op.exists (db_out_path) and db_in_path != db_out_path:
            logging.warning ('will delete existing db_out_path')
            os.remove (db_out_path)

        # copy input database into the output one
        if db_in_path != db_out_path:
            shutil.copyfile(db_in_path, db_out_path)

        self.conn = sqlite3.connect (db_out_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute('SELECT imagefile FROM images')
        image_entries = self.cursor.fetchall()

        button = 0
        for (imagefile,) in image_entries:

            imagepath = op.join (os.getenv('CITY_DATA_PATH'), imagefile)
            if not op.exists (imagepath):
                raise Exception ('image does not exist: ' + imagepath)
            self.img_show = cv2.imread(imagepath) if self.debug_show else None

            self.cursor.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
            car_entries = self.cursor.fetchall()
            logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

            for car_entry in car_entries:
                self.processCar (car_entry)

            if self.debug_show and button != 27: 
                cv2.imshow('debug_show', self.img_show)
                button = cv2.waitKey(-1)
                if button == 27: cv2.destroyWindow('debug_show')

        self.conn.commit()
        self.conn.close()



def __setupLogHeader__ (db_in_path, db_out_path, params, name):

    logging.info ('=== processing ' + name + '===')
    logging.info ('db_in_path:  ' + db_in_path)
    logging.info ('db_out_path: ' + db_out_path)
    logging.info ('params:      ' + str(params))



def __setupCopyDb__ (db_in_path, db_out_path):

    if not op.exists (db_in_path):
        raise Exception ('db does not exist: ' + db_in_path)

    if op.exists (db_out_path) and db_in_path != db_out_path:
        logging.warning ('will delete existing db_out_path')
        os.remove (db_out_path)

    if db_in_path != db_out_path:
        # copy input database into the output one
        shutil.copyfile(db_in_path, db_out_path)



def dbAssignOrientations (db_in_path, db_out_path, params):

    __setupLogHeader__ (db_in_path, db_out_path, params, 'dbAssignOrientations')
    __setupCopyDb__ (db_in_path, db_out_path)

    if not 'geom_maps_dir' in params.keys():
        raise Exception ('geom_maps_dir is not given in params')

    geom_maps_dir = params['geom_maps_dir']
    pitch_map_path = op.join (geom_maps_dir, 'pitchMap.tiff')
    yaw_map_path   = op.join (geom_maps_dir, 'yawMap.tiff')
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

    conn.commit()
    conn.close()



def dbMove (db_in_path, db_out_path, params):

    __setupLogHeader__ (db_in_path, db_out_path, params, 'dbMove')
    __setupCopyDb__ (db_in_path, db_out_path)

    conn = sqlite3.connect (db_out_path)
    cursor = conn.cursor()

    if 'new_images_dir' in params.keys():

        cursor.execute('SELECT imagefile FROM images')
        imagefiles = cursor.fetchall()

        for (oldfile,) in imagefiles:
            newfile = op.join (params['new_images_dir'], op.basename (oldfile))
            cursor.execute('UPDATE images SET imagefile=? WHERE imagefile=?', (newfile, oldfile))
            cursor.execute('UPDATE cars SET imagefile=? WHERE imagefile=?', (newfile, oldfile))
            if checkTableExists (cursor, 'masks'):
                cursor.execute('UPDATE masks SET imagefile=? WHERE imagefile=?', (newfile, oldfile))

    if 'new_mask_dir' in params.keys() and not checkTableExists (cursor, 'masks'):
        logging.warning ('new_mask_dir is in params, but table masks does not exist')
    elif 'new_mask_dir' in params.keys():
        cursor.execute('SELECT maskfile FROM masks')
        maskfiles = cursor.fetchall()

        for (oldfile,) in maskfiles:
            newfile = op.join (params['new_masks_dir'], op.basename (oldfile))
            cursor.execute('UPDATE masks SET maskfile=? WHERE maskfile=?', (newfile, imagefile))

    conn.commit()
    conn.close()

        

def dbMerge (db_in_paths, db_out_path, params = {}):

    assert (len(db_in_paths) == 2)   # 2 for now
    __setupLogHeader__ (db_in_path, db_out_path, params, 'dbMerge')
    __setupCopyDb__ (db_in_path, db_out_path)

    conn_out = sqlite3.connect (db_out_path)
    cursor_out = conn_out.cursor()

    conn_in = sqlite3.connect (db_in_paths[1])
    cursor_in = conn_in.cursor()

    cursor_in.execute('SELECT * FROM images')
    image_entries = cursor_in.fetchall()

    assert (not checkTableExists (cursor_in, 'matches'))   # for now

    # copy images and possibly masks
    for image_entry in image_entries:
        imagefile = image_entry[0]
        # check that doesn't exist
        cursor_out.execute('SELECT count(*) FROM images WHERE imagefile=?', (imagefile,))
        (num,) = cursor_out.fetchone()
        if num > 0:
            logging.warning ('duplicate image ' + imagefile + ' found in ' + db_in_paths[1]) 
            continue
        # insert image
        cursor_out.execute('INSERT INTO images VALUES (?,?,?,?);', image_entry)
        # insert mask
        if checkTableExists (cursor_in, 'masks'):
            cursor_in.execute('SELECT * FROM masks WHERE imagefile=?', (imagefile,))
            mask_entry = cursor_in.fetchone()
            cursor_out.execute('INSERT INTO masks VALUES (?,?);', mask_entry)
    
    cursor_in.execute('SELECT * FROM cars')
    car_entries = cursor_in.fetchall()

    # copy cars and possible polygons
    for car_entry in car_entries:
        carid = queryField (car_entry, 'id')
        s = 'cars(imagefile,name,x1,y1,width,height,offsetx,offsety,yaw,pitch)'
        cursor_out.execute('INSERT INTO ' + s + ' VALUES (?,?,?,?,?,?,?,?,?,?);', car_entry[1:])
        carid_new = cursor_out.lastrowid
        if checkTableExists (cursor_in, 'polygons'):
            cursor_in.execute('SELECT * FROM polygons WHERE carid=?', (carid,))
            polygon_entry = cursor_in.fetchone()
            x = polygon_entry[2]
            y = polygon_entry[3]
            cursor_out.execute('INSERT INTO polygons(carid,x,y) VALUES (?,?,?);', (carid_new,x,y))

    conn_out.commit()
    conn_out.close()
    conn_in.close()








class ManualClassifier (Processor):

    def __init__(self, params = {}):

        logging.info ('=== Manual.__init__ ===')
        logging.info ('params: ' + str(params))
        logging.info ('')

        self.debug_show = True

        if 'keys_config' in params.keys() or 'calibrate' not in params.keys(): 
            self.keys_config = params['keys_config']
        else:
            self.keys_config = getCalibration()
        logging.info ('left:  ' + str(self.keys_config['left']))
        logging.info ('right: ' + str(self.keys_config['right']))
        logging.info ('del:   ' + str(self.keys_config['del']))


    def processDb (self, db_in_path, db_out_path, params = {}):

        __setupLogHeader__ (db_in_path, db_out_path, params, 'ManualClassifier')
        __setupCopyDb__ (db_in_path, db_out_path)

        self.conn = sqlite3.connect (db_out_path)
        self.cursor = self.conn.cursor()

        if 'car_condition' in params.keys(): 
            car_condition = params['car_condition']
        else:
            car_condition = ''

        self.cursor.execute('SELECT imagefile FROM images')
        image_entries = self.cursor.fetchall()

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
            img = cv2.imread(imagepath) if self.debug_show else None

            self.cursor.execute('SELECT * FROM cars WHERE imagefile=? ' + car_condition, (imagefile,))
            car_entries = self.cursor.fetchall()
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

                if not carid in car_statuses.keys():
                    car_statuses[carid] = 'good'

                img_show = img.copy()
                self.debugShowAddRoi (img_show, roi, (offsety, offsetx), car_statuses[carid])

                cv2.imshow('show', img_show)
                button = cv2.waitKey(-1)

                self.keys_config[ord('c')] = 'car'
                self.keys_config[ord(' ')] = 'car'
                self.keys_config[ord('d')] = 'double'
                self.keys_config[ord('h')] = 'vehicle'
                self.keys_config[ord('t')] = 'taxi'
                self.keys_config[ord('r')] = 'truck'
                self.keys_config[ord('v')] = 'van'
                self.keys_config[ord('m')] = 'minivan'
                self.keys_config[ord('b')] = 'bus'
                self.keys_config[ord('p')] = 'pickup'
                self.keys_config[ord('o')] = 'object'

                if button == self.keys_config['left']:
                    logging.debug ('prev')
                    index_car -= 1
                elif button == self.keys_config['right']:
                    logging.debug ('next')
                    index_car += 1
                elif button == self.keys_config['del']:
                    logging.info ('delete')
                    car_statuses[carid] = 'badroi'
                    index_car += 1
                elif button in self.keys_config.keys():
                    logging.info (self.keys_config[button])
                    car_statuses[carid] = self.keys_config[button]
                    index_car += 1

            if button == self.keys_config['left']:
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
                deleteCar (self.cursor, carid)
            else:
                self.cursor.execute('UPDATE cars SET name=? WHERE id=?', (status, carid))

        self.conn.commit()
        self.conn.close()


