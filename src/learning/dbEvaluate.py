import os, os.path as op
import sys
import logging
import shutil
import glob
import json
import sqlite3
import cv2
import time
from helperImg    import ReaderVideo
from helperKeys   import KeyReaderUser
from helperSetup  import dbInit, setParamUnlessThere
from learning.violajones.opencvInterface import loadJson, ExperimentsBuilder
from dbUtilities  import bbox2roi, drawRoi, overlapRatio, expandRoiFloat, roi2bbox
from helperDb     import carField




def _evaluateForImage_ (cursor_eval, cursor_true, imagefile, params):
    setParamUnlessThere (params, 'debug',            False)
    setParamUnlessThere (params, 'image_processor',  ReaderVideo())
    setParamUnlessThere (params, 'key_reader',       KeyReaderUser())

    # roi-s from ground truth
    cursor_true.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
    car_entries = cursor_true.fetchall()
    logging.info ('found %d ground-true objects' % len(car_entries))
    truth = []
    for car_entry in car_entries:
        truth.append( bbox2roi (carField(car_entry, 'bbox')) )

    # roi-s from detections
    cursor_eval.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
    car_entries = cursor_eval.fetchall()
    logging.info ('found %d detected    objects' % len(car_entries))
    detected = []
    for car_entry in car_entries:
        detected.append( bbox2roi (carField(car_entry, 'bbox')) )

    # performance on this image
    hits   = 0
    misses_array = [True] * len(truth)
    falses = 0
    # TODO: get the best pairwise assignment (now, it's naive)
    statuses = {}
    for d in detected:
        best_dist = 1
        best_i = None
        for i in range(len(truth)):
            dist = 1 - overlapRatio(d, truth[i])
            if dist < best_dist:
                best_i = i
                best_dist = dist
        logging.debug('id: %d, its best distance: %f' % (carField(car_entry,'id'), best_dist) )
        if best_dist < params['dist_thresh']:
            hits += 1
            misses_array[best_i] = False
            statuses[tuple(d)] = True
        else:
            falses += 1
            statuses[tuple(d)] = False
    # get the number of misses from separate numbers
    misses = sum(misses_array)

    logging.info (op.basename(imagefile) + ': ' + str((hits, misses, falses)))

    # for detection multiple pos may stand for the same true (before NMS), so calculate fps:
    if truth:
        fps = float(len(truth) - misses) / len(truth)
        logging.info ('fps: %f' % fps)
    else:
        logging.info ('fps: no truth in this image')

    if params['debug']:
        img = params['image_processor'].imread(imagefile)
        for roi in detected:
            if statuses[tuple(roi)]:
                drawRoi (img, roi, '', (0,255,0))
            else:
                drawRoi (img, roi, '', (0,0,255))
        for roi in truth:
            drawRoi (img, roi, '', (255,0,0))
        cv2.imshow('evaluateDetector: green: matched, red: not matched, blue: truth', img)
        if params['key_reader'].readKey() == 27:
            cv2.destroyWindow('debug')
            params['debug'] = False

    return (hits, misses, falses)



def evaluateDetector (c, cursor_true, params):
    '''
    Compare bboxes for the ground truth db and the db under evaluation
    Returns a list of (hits, misses, false positives)
    '''
    logging.info ('==== evaluateDetector ====')
    setParamUnlessThere (params, 'dist_thresh', 0.5)

    c.execute('SELECT imagefile FROM images')
    image_entries = c.fetchall()

    # evaluate
    result = (0,0,0) 
    for (imagefile,) in image_entries:
        logging.debug ('evaluating image: ' + imagefile)
        result_im = _evaluateForImage_ (c, cursor_true, imagefile, params)
        result = tuple(map(sum,zip(result, result_im)))
    return result


def evaluateDetectorPath (c, db_true_path, params):
    '''
    Thin wrapper around 'evaluateDetector'.
    Open ground_truth db, and pass its cursor further
    '''

    # check ground truth db
    db_true_path = op.join (os.getenv('CITY_DATA_PATH'), db_true_path)
    if not op.exists (db_true_path):
        raise Exception ('db_true_path does not exist: ' + db_true_path)

    # connect and do work
    conn_true = sqlite3.connect (db_true_path)
    cursor_true = conn_true.cursor()
    result = evaluateDetectorFromConn (c, cursor_true, params)
    conn_true.close()

    return result




def dbEvaluateTask (task_path, db_true_path, db_eval_dir, params):
    '''
    A task is a json file in the 'tree' format.Each element must have 'model_name' field
    db_eval_dir must have db-s with names in the form: model_name.db
    '''

    # save results as lines in the output file
    if 'result_path' in params.keys():
        result_path = op.join (os.getenv('CITY_DATA_PATH'), params['result_path'])
        #if op.exists(result_path):
        #    os.remove(result_path)
        f = open(result_path, 'a')
        f.write('evaluated on: ' + db_true_path + '\n')

    # evaluate each db from the task
    for task in ExperimentsBuilder(loadJson(task_path)).getResult():
        model_dir = op.join (os.getenv('CITY_DATA_PATH'), task['model_dir'])
        if 'model_name' in task.keys():
            model_name = task['model_name']
        else:
            model_name = op.basename(task['model_dir'])

        db_in_path = op.join (db_eval_dir, model_name + '.db')
        if not op.exists( op.join(os.getenv('CITY_DATA_PATH'), db_in_path)):
            raise Exception ('db_in_path does not exist: ' + db_in_path)
        logging.info ('evaluating task: ' + op.basename(db_in_path))
        (conn, cursor) = dbInit(db_in_path)
        result = evaluateDetectorPath(cursor, db_true_path, params)
        conn.close()
        
        # (hits, misses, falses) to file
        f.write (op.basename(db_in_path) + ': \t' + str(result) + '\n')

    f.close()


def dbDisplayTask (task_path):
    experiments = ExperimentsBuilder(loadJson(task_path)).getResult()
    print (json.dumps(experiments, indent=4))

