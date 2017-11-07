#! /usr/bin/env python
from __future__ import print_function

import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))

import argparse
import logging
import numpy as np
import tensorflow as tf
from time import time
from progressbar import ProgressBar
from keras.applications.inception_v3 import InceptionV3
from keras.applications.inception_v3 import preprocess_input
from keras.preprocessing import image
from keras.models import Model, load_model
from keras.layers import Dense, GlobalAveragePooling2D
from keras import backend as K
from keras.optimizers import SGD
from scipy.misc import imresize
from db.lib.dbDataset import CitycarsDataset
from db.lib.helperDb import carField
from db.lib.helperSetup import dbInit
from dataset_utilities import BatchGenerator, one_hot_to_angle

parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--out_db_file', required=True)
parser.add_argument('--in_h5_file', required=True)
parser.add_argument('--logging', default=20, type=int)
args = parser.parse_args()

logging.basicConfig(level=args.logging)

print ('Loading model... ', end='')
start = time()
model = load_model(args.in_h5_file)
print ('done in %.1f sec.' % (time() - start))

dataset = CitycarsDataset(args.in_db_file, fraction=1., crop_car=False, randomly=False)
(conn, c) = dbInit(args.in_db_file, args.out_db_file)

for image, car_entry in ProgressBar()(dataset.__getitem__()):
  image = imresize(image, (139,139))
  image = image.astype(float)
  image = preprocess_input(image)
  image = np.expand_dims(image, axis=0)
  pred = one_hot_to_angle(model.predict(image))
  carid = carField(car_entry, 'id')
  logging.debug('carid %d predicted %f' % (carid, pred))
  c.execute('UPDATE cars SET yaw=? WHERE id=?', (pred, carid))

conn.commit()
conn.close()
