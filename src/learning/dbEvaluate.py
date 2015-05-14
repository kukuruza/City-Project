import logging
import sys
import os, os.path as op
import shutil
import glob
import json
import sqlite3
import cv2
import time
from opencvInterface import loadJson, execCommand, ExperimentsBuilder
from utilities import bbox2roi, drawRoi, overlapRatio, expandRoiFloat, roi2bbox
from dbInterface import queryField



def __evaluateForImage__ (cursor_true, cursor_eval, imagefile, params):

    # roi-s from ground truth
    cursor_true.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
    car_entries = cursor_true.fetchall()
    truth = []
    for car_entry in car_entries:
        truth.append( bbox2roi (queryField(car_entry, 'bbox')) )

    # roi-s from detections
    cursor_eval.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
    car_entries = cursor_eval.fetchall()
    detected = []
    for car_entry in car_entries:
        detected.append( bbox2roi (queryField(car_entry, 'bbox')) )

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
        img = cv2.imread(op.join (os.getenv('CITY_DATA_PATH'), imagefile))
        for roi in detected:
            if statuses[tuple(roi)]:
                drawRoi (img, roi, '', (0,255,0))
            else:
                drawRoi (img, roi, '', (0,0,255))
        for roi in truth:
            drawRoi (img, roi, '', (255,0,0))
        cv2.imshow('green - matched, red - not matched, blue - ground truth', img)
        cv2.waitKey(-1)

    return (hits, misses, falses)



def dbEvaluateDetector (db_true_path, db_eval_path, params):
    '''
    Compare bboxes for the ground truth db and the db under evaluation
    Returns a list of (hits, misses, false positives)
    '''

    params = setupHelper.setParamUnlessThere (params, 'debug_show', False)
    params = setupHelper.setParamUnlessThere (params, 'dist_thresh', 0.5)

    # open ground truth db
    db_true_path = op.join (os.getenv('CITY_DATA_PATH'), db_true_path)
    if not op.exists (db_true_path):
        raise Exception ('db_true_path does not exist: ' + db_true_path)
    conn_true = sqlite3.connect (db_true_path)
    cursor_true = conn_true.cursor()

    # open evalutaed db
    db_eval_path = op.join (os.getenv('CITY_DATA_PATH'), db_eval_path)
    if not op.exists (db_eval_path):
        raise Exception ('db_true_path does not exist: ' + db_eval_path)
    conn_eval = sqlite3.connect (db_eval_path)
    cursor_eval = conn_eval.cursor()

    cursor_eval.execute('SELECT imagefile FROM images')
    image_entries = cursor_eval.fetchall()

    # evaluate
    result = (0,0,0) 
    for (imagefile,) in image_entries:
        logging.debug ('evaluating image: ' + imagefile)
        result_im = __evaluateForImage__ (cursor_true, cursor_eval, imagefile, params)
        result = tuple(map(sum,zip(result, result_im)))

    conn_true.close()
    conn_eval.close()

    return result




def dbEvaluateTask (task_path, db_true_path, db_eval_dir, params):
    '''
    A task is a json file in the 'tree' format.Each element must have 'model_name' field
    db_eval_dir must have db-s with names in the form: model_name.db
    '''

    CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')

    # save results as lines in the output file
    if 'result_path' in params.keys():
        result_path = op.join (CITY_DATA_PATH, params['result_path'])
        #if op.exists(result_path):
        #    os.remove(result_path)
        f = open(result_path, 'a')
        f.write('evaluated on: ' + db_true_path + '\n')

    # evaluate each db from the task
    for task in ExperimentsBuilder(loadJson(task_path)).getResult():
        model_dir = op.join (CITY_DATA_PATH, task['model_dir'])
        if 'model_name' in task.keys():
            model_name = task['model_name']
        else:
            model_name = op.basename(task['model_dir'])

        db_eval_path = op.join (db_eval_dir, model_name + '.db')
        if not op.exists( op.join(CITY_DATA_PATH, db_eval_path)):
            raise Exception ('db_eval_path does not exist: ' + db_eval_path)
        logging.info ('evaluating task: ' + op.basename(db_eval_path))
        result = dbEvaluateDetector (db_true_path, db_eval_path, params)
        
        # (hits, misses, falses) to file
        f.write (op.basename(db_eval_path) + ': \t' + str(result) + '\n')

    f.close()


def dbDisplayTask (task_path):
    experiments = ExperimentsBuilder(loadJson(task_path)).getResult()
    print (json.dumps(experiments, indent=4))



