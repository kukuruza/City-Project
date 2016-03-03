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
from learning.helperSetup import setParamUnlessThere
from opencvInterface      import loadJson, execCommand, ExperimentsBuilder
from learning.dbUtilities import *
from learning.helperDb    import queryField, doesTableExist



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



def detectViolajones (c, model_path, params):
    logging.info ('==== detectViolajones ====')
    setParamUnlessThere (params, 'debug_show', False)

    # model
    logging.info ('model_path: ' + model_path)
    model_path = op.join (os.getenv('CITY_DATA_PATH'), model_path)
    if not op.exists(model_path):
        raise Exception ('model_path does not exist: ' + model_path)

    cascade = cv2.CascadeClassifier (model_path)

    # remove the ground truth
    c.execute('DELETE FROM cars')
    if doesTableExist(c, 'matches'):
        c.execute('DELETE FROM matches')
    if doesTableExist(c, 'polygons'):
        c.execute('DROP TABLE polygons')

    c.execute('SELECT imagefile FROM images')
    image_entries = c.fetchall()

    # TODO: how to estimate score from Viola-Jones?

    # detect
    for (imagefile,) in image_entries:
        bboxes = __detectForImage__ (c, cascade, imagefile, params)
        for bbox in bboxes:
            entry = (imagefile, 'vehicle', bbox[0], bbox[1], bbox[2], bbox[3], 1)
            s = 'cars(imagefile,name,x1,y1,width,height,score)'
            c.execute('INSERT INTO ' + s + ' VALUES (?,?,?,?,?,?,?);', entry)

        if params['debug_show'] and ('key' not in locals() or key != 27): 
            img = cv2.imread(op.join(os.getenv('CITY_DATA_PATH'), imagefile))
            for bbox in bboxes:
                drawScoredRoi (img, bbox2roi(bbox), '', 1)
            cv2.imshow('debug_show', img)
            key = cv2.waitKey(-1)
            if key == 27: cv2.destroyWindow('debug_show')



def detectViolajonesTask (db_in_path, task_path, db_out_dir, params):
    '''
    Perform Viola-Jones detection of each model in the task
    '''

    for experiment in ExperimentsBuilder(loadJson(task_path)).getResult():
        model_dir = experiment['model_dir']
        if 'model_name' in experiment.keys():
            model_dir = op.join(model_dir, experiment['model_name'])
        model_path = op.join(model_dir, 'cascade.xml')
        db_out_path = op.join(db_out_dir, op.basename(model_dir) + '.db')

        params = dict(params.items() + experiment.items())

        # detect
        ViolajonesProcessor(db_in_path, db_out_path).detectViolajones(model_path, params).commit()
