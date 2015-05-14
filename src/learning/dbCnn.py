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



class CnnProcessor (BaseProcessor):

    def importLabels (self, labels_path, params = {}):
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
