import logging
import sys
import os, os.path as op
import shutil
import glob
import json
import sqlite3
import cv2
import time
from optparse import OptionParser

sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
from setup_helper import setupLogging, get_CITY_DATA_PATH, setParamUnlessThere
from opencvInterface import loadJson, execCommand, ExperimentsBuilder
from utilities import bbox2roi, __drawRoi__, overlapRatio
from dbInterface import queryField



def __evaluateForImage__ (cursor, cascade, imagefile, params):
    logging.info ('evaluating image: ' + imagefile)

    cursor.execute('SELECT ghostfile FROM images WHERE imagefile=?', (imagefile,))
    (ghostfile,) = cursor.fetchone()

    ghostpath = op.join (os.getenv('CITY_DATA_PATH'), ghostfile)
    if not op.exists(ghostpath):
        raise Exception ('ghostpath does not exist: ' + ghostpath)
    img = cv2.imread(ghostpath)

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

    # performance on this image
    hits   = 0
    misses = len(truth)
    falses = 0
    # TODO: get the best pairwise assignment (now, it's naive)
    for d in detected:
        best_dist = 0
        for t in truth:
            best_dist = max (overlapRatio(d,t), best_dist)
        if best_dist < params['dist_thresh']:
            hits += 1
            misses -= 1
        else:
            falses += 1

    if params['debug_show']:
        for roi in detected:
            __drawRoi__ (img, roi, (0, 0), '', (0,0,255))
        for roi in truth:
            __drawRoi__ (img, roi, (0, 0), '', (255,0,0))
        cv2.imshow('red - detected, blue - ground truth', img)
        cv2.waitKey(-1)

    logging.info ('image result: '+str(hits)+', '+str(misses)+', '+str(falses))

    return (hits, misses, falses)


def dbTestCascade (experiment, db_path, params = {}):

    CITY_DATA_PATH = get_CITY_DATA_PATH()

    params = setParamUnlessThere (params, 'debug_show', False)
    params = setParamUnlessThere (params, 'dist_thresh', 0.5)
    #experiment = setParamUnlessThere (experiment, 'feature_type', 'HAAR')
    #experiment = setParamUnlessThere (experiment, 'min_hit_rate', 0.995)
    #experiment = setParamUnlessThere (experiment, 'max_false_alarm_rate', 0.5)

    # labelled data
    db_path = op.join (CITY_DATA_PATH, db_path)

    # model
    model_path = op.join (CITY_DATA_PATH, experiment['model_dir'], 'cascade.xml')
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

    print (result)

    conn.close()



if __name__ == '__main__':

    setupLogging ('log/detector/runTestTask.log', logging.INFO, 'a')

    parser = OptionParser(description='Evaluate cascade detector')
    parser.add_option('--task_path', type=str, nargs='?',
                      default='learning/violajones/tasks/test-trained.json',
                      help='path to json file with task description')
    parser.add_option('--db_path', type=str, nargs='?',
                      default='datasets/labelme/Databases/distinct-frames.db')
    parser.add_option('--show_experiments', action='store_true',
                      default=False,
                      help='print out experiment configurations and then quit')
    (options, args) = parser.parse_args()
    logging.info ('argument list: ' + str(options))

    if options.show_experiments:
        experiments = ExperimentsBuilder(loadJson(options.task_path)).getResult()
        print (json.dumps(experiments, indent=4))
        sys.exit()

    params = { 'debug_show': False }

    for experiment in ExperimentsBuilder(loadJson(options.task_path)).getResult():
        dbTestCascade (experiment, options.db_path, params)


