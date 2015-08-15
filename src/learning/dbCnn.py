import logging
import os, sys
import os.path as op
import shutil
import glob
import json
import sqlite3
import numpy as np, cv2
from dbInterface import queryCars, queryField
from utilities import bbox2roi
from dbBase import BaseProcessor
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/cnn'))
from DeploymentPatches import DeploymentPatches


class CnnProcessor (BaseProcessor):

    def __init__ (self, db_in_path, db_out_path = None, params = {}):
        super(CnnProcessor, self).__init__ (db_in_path, db_out_path)

        self.verifyParamThere (params, 'network_path')
        self.verifyParamThere (params, 'model_path')

        self.deployment = DeploymentPatches(params['network_path'], params['model_path'])



    def importLabels (self, labels_path, params = {}):
        '''
        This function is from the times when deployment gave a text file with labels
        Will be removed later
        '''
        logging.info ('==== importLabels ====')
        c = self.cursor

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
    
        return self


    def classifyDb (self, params):
        '''
        Use CNN python interface to classify .db
        '''
        logging.info ('==== dbCnn.classifyDb ====')
        c = self.cursor

        self.verifyParamThere (params, 'resize')
        assert (type(params['resize']) == list and len(params['resize']) == 2)

        c.execute('SELECT * FROM cars')
        car_entries = c.fetchall()

        for car_entry in car_entries:

            # get the ghost
            imagefile = queryField(car_entry, 'imagefile')
            c.execute('SELECT ghostfile FROM images WHERE imagefile = ?', (imagefile,))
            (ghostfile,) = c.fetchone()
            ghostpath = op.join (self.CITY_DATA_PATH, imagefile)
            if not op.exists (ghostpath):
                raise Exception ('ghostfile does not exist: %s' % ghostpath)
            ghost = cv2.imread(ghostpath)

            # extract patch
            bbox = queryField(car_entry, 'bbox')
            roi = bbox2roi(bbox)
            patch = ghost [roi[0]:roi[2]+1, roi[1]:roi[3]+1]
            # resize
            patch = cv2.resize(patch, tuple(params['resize']))

            # work horse
            label = self.deployment.classify(patch)

            # save label
            carid = queryField(car_entry, 'id')
            c.execute('UPDATE cars SET name=? WHERE id=?', (label, carid))


        return self

