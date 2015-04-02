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
from utilities import bbox2roi, drawRoi, overlapRatio, expandRoiFloat
from dbInterface import queryField



def __evaluateForImage__ (cursor, cascade, imagefile, params):
    logging.info ('evaluating image: ' + imagefile)

    cursor.execute('SELECT ghostfile FROM images WHERE imagefile=?', (imagefile,))
    (ghostfile,) = cursor.fetchone()

    ghostpath = op.join (os.getenv('CITY_DATA_PATH'), ghostfile)
    if not op.exists(ghostpath):
        raise Exception ('ghostpath does not exist: ' + ghostpath)
    img = cv2.imread(ghostpath)
    (width, height, depth) = img.shape

    # roi-s from ground truth
    cursor.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
    car_entries = cursor.fetchall()
    truth = []
    for car_entry in car_entries:
        truth.append( bbox2roi (queryField(car_entry, 'bbox')) )

    # roi-s from detecting
    logging.debug ('started detectMultiScale')
    start = time.time()
    detected_bboxes = cascade.detectMultiScale(img)
    end = time.time()
    logging.debug ('finished detectMultiScale in sec: ' + str(end - start))
    detected = [bbox2roi(list(bbox)) for bbox in detected_bboxes]
    contraction = -params['expanded'] / (1 + params['expanded'])
    detected = [expandRoiFloat(bbox, (width,height), (contraction,contraction))
                for bbox in detected]

    # performance on this image
    hits   = 0
    misses = len(truth)
    falses = 0
    # TODO: get the best pairwise assignment (now, it's naive)
    for d in detected:
        best_dist = 1
        for t in truth:
            best_dist = min (1 - overlapRatio(d,t), best_dist)
        if best_dist < params['dist_thresh']:
            hits += 1
            misses -= 1
        else:
            falses += 1

    logging.info ('image result: '+str(hits)+', '+str(misses)+', '+str(falses))

    if params['debug_show']:
        for roi in detected:
            drawRoi (img, roi, (0, 0), '', (0,0,255))
        for roi in truth:
            drawRoi (img, roi, (0, 0), '', (255,0,0))
        cv2.imshow('red - detected, blue - ground truth', img)
        cv2.waitKey(-1)

    return (hits, misses, falses)


def dbEvaluateCascade (db_path, params):

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()

    params = setupHelper.setParamUnlessThere (params, 'debug_show', False)
    params = setupHelper.setParamUnlessThere (params, 'dist_thresh', 0.5)
    params = setupHelper.setParamUnlessThere (params, 'expanded', 0)
    params = setupHelper.setParamUnlessThere (params, 'num_stages', -1)

    # labelled data
    db_path = op.join (CITY_DATA_PATH, db_path)
    if not op.exists (db_path):
        raise Exception ('db_path does not exist: ' + db_path)

    # model
    model_path = op.join (CITY_DATA_PATH, params['model_dir'], 'cascade.xml')
    logging.info ('model_path: ' + model_path)
    cascade = cv2.CascadeClassifier (model_path)

    conn = sqlite3.connect (db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT imagefile FROM images')
    image_entries = cursor.fetchall()

    # evaluate
    result = (0,0,0) 
    for (imagefile,) in image_entries:
        result_im = __evaluateForImage__ (cursor, cascade, imagefile, params)
        result = tuple(map(sum,zip(result, result_im)))

    print (op.basename(params['model_dir']) + ': ' + str(result))

    conn.close()



def evaluateTask (task_path, db_eval_path, params):

    params = setupHelper.setParamUnlessThere (params, 'show_experiments', False)

    if params['show_experiments']:
        experiments = ExperimentsBuilder(loadJson(task_path)).getResult()
        print (json.dumps(experiments, indent=4))
        return

    for experiment in ExperimentsBuilder(loadJson(task_path)).getResult():
        params = dict(params.items() + experiment.items())
        dbEvaluateCascade (db_eval_path, params)
