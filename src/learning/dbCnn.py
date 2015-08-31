import logging
import os, sys
import os.path as op
import shutil
import glob
import json
import sqlite3
import numpy as np, cv2
from dbInterface import carField
from utilities import bbox2roi
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/cnn'))
from DeploymentPatches import DeploymentPatches
import helperSetup


def importLabels (c, labels_path, params = {}):
    '''
    This function is from the times when deployment gave a text file with labels
    Will be removed later
    '''
    logging.info ('==== importLabels ====')

    labels_path = op.join (os.getenv('CITY_DATA_PATH'), labels_path)

    predictions = { }
    with open(labels_path) as f:
        for line in f:
            words = line.split()
            carid = int(op.splitext(words[0])[0])
            label = int(words[1])
            predictions[carid] = label
            logging.debug('carid: ' + str(carid) + ', label: ' + str(label))

    c.execute ('SELECT id FROM cars')
    carids = c.fetchall();
    
    # iterate over db instead of labels because we may have filtered db
    for (carid,) in carids:
        if carid in predictions.keys():
            label = predictions[carid]
            c.execute ('UPDATE cars SET score = ? WHERE id = ?', (label,carid))
        else:
            logging.error ('carid: ' + str(carid) + ' is not labelled')
            c.execute ('UPDATE cars SET score = 0.5 WHERE id = ?', (carid,))

    logging.info ('num labels: ' + str(len(predictions)))
    logging.info ('num cars:   ' + str(len(carids)))




class CnnClassifier:

    def __init__ (self, network_path, model_path):

        network_path = op.join(os.getenv('CITY_DATA_PATH', network_path)
        model_path   = op.join(os.getenv('CITY_DATA_PATH', model_path)

        self.deployment = DeploymentPatches(network_path, model_path)


    def classifyDb (c, params):
        '''
        Use CNN python interface to classify .db
        '''
        logging.info ('==== dbCnn.classifyDb ====')
        helperSetup.assertParamIsThere (params, 'resize')
        assert (type(params['resize']) == list and len(params['resize']) == 2)

        c.execute('SELECT * FROM cars')
        car_entries = c.fetchall()

        for car_entry in car_entries:

            # get the image
            imagefile = carField(car_entry, 'imagefile')
            imagepath = op.join (os.getenv('CITY_DATA_PATH'), imagefile)
            if not op.exists (imagepath):
                raise Exception ('imagepath does not exist: %s' % imagepath)
            image = cv2.imread(imagepath)

            # extract patch
            bbox = carField(car_entry, 'bbox')
            roi = bbox2roi(bbox)
            patch = image [roi[0]:roi[2]+1, roi[1]:roi[3]+1]
            # resize
            patch = cv2.resize(patch, tuple(params['resize']))

            # work horse
            label = self.deployment.classify(patch)

            # save label
            carid = carField(car_entry, 'id')
            c.execute('UPDATE cars SET name=? WHERE id=?', (label, carid))

