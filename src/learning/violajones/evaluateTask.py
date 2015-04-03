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
    logging.debug ('evaluating image: ' + imagefile)

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
    logging.debug('contraction: ' + str(contraction))
    detected = [expandRoiFloat(bbox, (width,height), (contraction,contraction))
                for bbox in detected]

    # performance on this image
    hits   = 0
    misses = len(truth)
    falses = 0
    # TODO: get the best pairwise assignment (now, it's naive)
    statuses = {}
    for d in detected:
        best_dist = 1
        for t in truth:
            best_dist = min (1 - overlapRatio(d,t), best_dist)
        if best_dist < params['dist_thresh']:
            hits += 1
            misses -= 1
            statuses[tuple(d)] = True
        else:
            falses += 1
            statuses[tuple(d)] = False

    logging.info (op.basename(imagefile) + ': ' + str((hits, misses, falses)))

    if params['debug_show']:
        for roi in detected:
            if statuses[tuple(roi)]:
                drawRoi (img, roi, (0, 0), '', (0,255,0))
            else:
                drawRoi (img, roi, (0, 0), '', (0,0,255))
        for roi in truth:
            drawRoi (img, roi, (0, 0), '', (255,0,0))
        cv2.imshow('green - matched, red - not matched, blue - ground truth', img)
        cv2.waitKey(-1)

    return (hits, misses, falses)


def dbEvaluateCascade (db_path, params):

    print ('evaluating model: ' + params['model_dir'])

    CITY_DATA_PATH = setupHelper.get_CITY_DATA_PATH()

    params = setupHelper.setParamUnlessThere (params, 'debug_show', False)
    params = setupHelper.setParamUnlessThere (params, 'dist_thresh', 0.5)
    params = setupHelper.setParamUnlessThere (params, 'num_stages', -1)
    params = setupHelper.setParamUnlessThere (params, 'model_name', '')

    # labelled data
    db_path = op.join (CITY_DATA_PATH, db_path)
    if not op.exists (db_path):
        raise Exception ('db_path does not exist: ' + db_path)

    # model
    model_dir = op.join (CITY_DATA_PATH, params['model_dir'], params['model_name'])
    model_path = op.join (model_dir, 'cascade.xml')
    logging.info ('model_path: ' + model_path)
    logging.debug ('model name: ' + op.basename(model_dir.rstrip('/')))
    if 'model' in params.keys() and op.basename(model_dir.rstrip('/')) != params['model']:
        return

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

    conn.close()

    result_str = op.basename(params['model_dir']) + ':\t' + ' '.join([str(s) for s in list(result)])
    print ('result ' + result_str)

    if 'result_path' in params.keys():
        with open(op.join (CITY_DATA_PATH, params['result_path']), 'a') as fresult:
            fresult.write (result_str + '\n')

    return result_str



def evaluateTask (task_path, db_eval_path, params):

    params = setupHelper.setParamUnlessThere (params, 'show_experiments', False)

    # when 'show_experiments' flag set, just display experiments and quit
    if params['show_experiments']:
        experiments = ExperimentsBuilder(loadJson(task_path)).getResult()
        print (json.dumps(experiments, indent=4))
        return

    # clear (by removing) the file of output

    if 'result_path' in params.keys():
        result_path = op.join (CITY_DATA_PATH, params['result_path'])
        if op.exists(result_path):
            os.remove(result_path)

    for experiment in ExperimentsBuilder(loadJson(task_path)).getResult():
        params = dict(params.items() + experiment.items())
        dbEvaluateCascade (db_eval_path, params)
