import logging
import sys
import os, os.path as op
import shutil
import glob
import json
import sqlite3
import cv2
import time

sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
import setupHelper
from opencvInterface import loadJson, execCommand, ExperimentsBuilder
from utilities import bbox2roi, drawRoi, overlapRatio, expandRoiFloat, roi2bbox
from dbInterface import queryField, checkTableExists
import processing



def __detectForImage__ (cursor, cascade, imagefile, params):
    logging.debug ('detecting for image: ' + imagefile)

    cursor.execute('SELECT ghostfile FROM images WHERE imagefile=?', (imagefile,))
    (ghostfile,) = cursor.fetchone()

    ghostpath = op.join (os.getenv('CITY_DATA_PATH'), ghostfile)
    if not op.exists(ghostpath):
        raise Exception ('ghostpath does not exist: ' + ghostpath)
    img = cv2.imread(ghostpath)
    (width, height, depth) = img.shape

    # bboxes-s from detecting
    logging.debug ('started detectMultiScale')
    start = time.time()
    detected = cascade.detectMultiScale(img)
    end = time.time()
    logging.debug ('finished detectMultiScale in sec: ' + str(end - start))
    contraction = -params['expanded'] / (1 + params['expanded'])
    logging.debug('contraction: ' + str(contraction))
    c = (contraction, contraction);
    detected = [roi2bbox( expandRoiFloat(bbox2roi(list(bbox)), (width,height), c) )
                for bbox in detected]

    logging.info (op.basename(imagefile) + ': detected bboxes: ' + str(len(detected)))

    return detected



def dbDetectCascade (db_in_path, db_out_path, model_path, params):

    CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')
    db_in_path   = op.join(CITY_DATA_PATH, db_in_path)
    db_out_path  = op.join(CITY_DATA_PATH, db_out_path)

    setupHelper.setupLogHeader (db_in_path, db_out_path, params, 'dbDetectCascade')
    setupHelper.setupCopyDb (db_in_path, db_out_path)

    conn = sqlite3.connect (db_out_path)
    cursor = conn.cursor()

    params = setupHelper.setParamUnlessThere (params, 'debug_show', False)

    # model
    model_path = op.join (CITY_DATA_PATH, model_path)
    logging.info ('model_path: ' + model_path)

    cascade = cv2.CascadeClassifier (model_path)

    # remove the ground truth
    cursor.execute('DELETE FROM cars')
    if checkTableExists(cursor, 'matches'):
        cursor.execute('DELETE FROM matches')
    if checkTableExists(cursor, 'polygons'):
        cursor.execute('DROP TABLE polygons')

    cursor.execute('SELECT imagefile FROM images')
    image_entries = cursor.fetchall()

    # TODO: how to estimate score from Viola-Jones?

    # detect
    button = 0
    for (imagefile,) in image_entries:
        bboxes = __detectForImage__ (cursor, cascade, imagefile, params)
        for bbox in bboxes:
            entry = (imagefile, 'vehicle', bbox[0], bbox[1], bbox[2], bbox[3], 1)
            s = 'cars(imagefile,name,x1,y1,width,height,score)'
            cursor.execute('INSERT INTO ' + s + ' VALUES (?,?,?,?,?,?,?);', entry)

        if params['debug_show'] and button != 27:
            img = cv2.imread(op.join(CITY_DATA_PATH, imagefile))
            for bbox in bboxes:
                drawRoi (img, bbox2roi(bbox), '', (255,0,0))
            cv2.imshow('detected', img)
            button = cv2.waitKey(-1)
            if button == 27: cv2.destroyWindow('debug_show')

    conn.commit()
    conn.close()



def dbDetectCascadeTask (db_in_path, task_path, db_out_dir, params):
    '''
    Perform Viola-Jones detection of each model in the task
    '''

    # clear db_out_dir
    db_out_dir = op.join (os.getenv('CITY_DATA_PATH'), db_out_dir)
    if op.exists(db_out_dir):
        shutil.rmtree(db_out_dir)
    os.makedirs(db_out_dir)

    for experiment in ExperimentsBuilder(loadJson(task_path)).getResult():
        model_dir = op.join (os.getenv('CITY_DATA_PATH'), experiment['model_dir'])
        if 'model_name' in experiment.keys():
            model_dir = op.join(model_dir, experiment['model_name'])
        model_path = op.join(model_dir, 'cascade.xml')
        db_out_path = op.join(db_out_dir, op.basename(model_dir) + '.db')

        if not op.exists(model_path):
            raise Exception ('model_path does not exist: ' + model_path)

        params = dict(params.items() + experiment.items())

        # detect
        dbDetectCascade(db_in_path, db_out_path, model_path, params)

        # filter
        processing.dbFilter (db_out_path, db_out_path, params)

