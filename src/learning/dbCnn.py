import os, sys, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/backend'))
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/cnn'))
import logging
import shutil
import glob
import json
import sqlite3
import numpy as np, cv2
from helperDb import carField
from utilities import bbox2roi
from DeploymentPatches import DeploymentPatches
import helperSetup
import helperImg


class DbCnn:
    '''
    This class is a wrapper around cnn/DeploymentPatches that can talk to db.
    '''

    def __init__ (self, network_path, model_path):
        self.deployment = DeploymentPatches(network_path, model_path)


    def classify (self, c, params):
        '''
        Use CNN python interface to classify .db
        '''
        logging.info ('==== DbCnn.classifyDb ====')
        helperSetup.assertParamIsThere  (params, 'resize') # (width,height)
        helperSetup.setParamUnlessThere (params, 'label_dict', {})
        helperSetup.setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
        helperSetup.setParamUnlessThere (params, 'image_processor', helperImg.ReaderVideo())
        assert isinstance(params['resize'], tuple) and len(params['resize']) == 2

        c.execute('SELECT * FROM cars')
        for car_entry in c.fetchall():

            # get the image
            imagefile = carField(car_entry, 'imagefile')
            image = params['image_processor'].imread(imagefile)

            # extract patch
            bbox = carField(car_entry, 'bbox')
            roi = bbox2roi(bbox)
            patch = image [roi[0]:roi[2]+1, roi[1]:roi[3]+1]
            patch = cv2.resize(patch, params['resize'])

            # work horse
            label = int(self.deployment.forward(patch)[0])

            # transform cnn label to its meaning
            if label in params['label_dict']:
                label = params['label_dict'][label]

            # save label
            carid = carField(car_entry, 'id')
            c.execute('UPDATE cars SET name=? WHERE id=?', (label, carid))
            logging.info('classified carid %d as %s' % (carid, label))

