import os, sys, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/backend'))
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/detector/fasterRcnn'))
import numpy as np
import cv2
import logging
import glob
import shutil
import sqlite3
from helperDb import carField
import helperDb
import utilities
from utilities import bbox2roi, roi2bbox, drawRoi
import helperSetup
import helperImg
from FasterRcnnDetector import FasterRcnnExtractor
import StringIO


def extractFeatures (c, out_file, params = {}):
    '''
    Extract features for every roi in a db
    '''
    logging.info ('==== extractFeatures ====')
    helperSetup.setParamUnlessThere (params, 'constraint', '1')
    helperSetup.setParamUnlessThere (params, 'cpu_mode', True)
    helperSetup.setParamUnlessThere (params, 'features_layer', 'fc6')
    helperSetup.assertParamIsThere  (params, 'model_dir')
    helperSetup.setParamUnlessThere (params, 'relpath',         os.getenv('CITY_DATA_PATH'))
    helperSetup.setParamUnlessThere (params, 'image_processor', helperImg.ReaderVideo())

    # set up the output
    out_path = op.join(params['relpath'], out_file)
    fid = open(out_path, 'w')

    # the workhorse
    extractor = FasterRcnnExtractor (params['model_dir'], params['cpu_mode'])
    extractor.features_layer = params['features_layer']

    c.execute ('SELECT imagefile FROM images')
    for (imagefile,) in c.fetchall():

        s = 'SELECT * FROM cars WHERE imagefile = ? AND (%s)' % params['constraint']
        c.execute (s, (imagefile,))
        car_entries = c.fetchall()

        logging.info ('image %s has %d cars' % (imagefile, len(car_entries)))

        # net crashes on empty bboxes array
        if not car_entries:
            logging.debug ('will skip this image')
            continue

        # collect bboxes from all cars
        bboxes = []
        carids = []
        for car_entry in car_entries:
            bboxes.append (carField(car_entry, 'bbox'))
            carids.append (carField(car_entry, 'id'))

        # load the image
        img = params['image_processor'].imread(imagefile)

        # extract features
        features = extractor.extract_features (img, bboxes)
        #features = np.zeros((len(bboxes), 8), dtype=float)
        #print 'features shape: ', features.shape

        # write ids and features
        assert len(carids) == features.shape[0]
        for i in range(len(carids)):
            s = StringIO.StringIO()
            np.savetxt(s, features[i,:], fmt = '%f', newline=' ')
            fid.write('%08d %s\n' % (carids[i], s.getvalue()))

    fid.close()
