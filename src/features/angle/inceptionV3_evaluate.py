#! /usr/bin/env python
from __future__ import print_function
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import argparse
import logging
import numpy as np
import tensorflow as tf
from time import time
from keras.applications.inception_v3 import InceptionV3
from keras.applications.inception_v3 import preprocess_input
from keras.preprocessing import image
from keras.models import Model, load_model
from keras.layers import Dense, GlobalAveragePooling2D
from keras import backend as K
from keras.optimizers import SGD
from scipy.misc import imresize
from db.lib.dbDataset import CitycarsDataset
from dataset_utilities import BatchGenerator, car_to_angle

parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--in_h5_file', required=True)
parser.add_argument('--logging', default=20, type=int)
args = parser.parse_args()

logging.basicConfig(level=args.logging)


dataset = CitycarsDataset(args.in_db_file, fraction=1., crop_car=False, randomly=False)

print ('Loading model... ', end='')
sys.stdout.flush()
start = time()
model = load_model(args.in_h5_file)
print ('done in %.1f sec.' % (time() - start))

# we need to recompile the model for these modifications to take effect
# we use SGD with a low learning rate
model.compile(optimizer=SGD(lr=0.0001, momentum=0.9),
              loss='categorical_crossentropy',
              metrics=['categorical_accuracy'])

batchsize = 16
print ('Evaluating...')
scores = model.evaluate_generator(iter(
  BatchGenerator(dataset, batchsize)), len(dataset) // batchsize)
print (model.metrics_names[0], scores[0])
print (model.metrics_names[1], scores[1])

dataset = CitycarsDataset(args.in_db_file, fraction=1., crop_car=False, randomly=False,
                          car_constraint='yaw IS NOT NULL')

start = time()
num_correct = 0
for ibatch, (images, car_entries) in enumerate(dataset.get_batch((139,139), batchsize)):
  gts = np.array([car_to_angle(car_entry) for car_entry in car_entries])
  images = images.astype(float)
  images = preprocess_input(images)
  pred = model.predict_on_batch(images).argmax(axis=1)
  logging.debug(str(np.column_stack((gts, pred))))
  num_correct += np.count_nonzero(pred == gts)
print ('By batch done in %.1f sec.' % (time() - start), end='')
print ('Out of %d, have %d correct' % ((ibatch+1) * batchsize, num_correct))

start = time()
num_correct = 0
for iframe, (image, car_entry) in enumerate(dataset.__getitem__()):
  gts = car_to_angle(car_entry)
  image = imresize(image, (139,139))
  image = image.astype(float)
  image = preprocess_input(image)
  image = np.expand_dims(image, axis=0)
  pred = model.predict(image).argmax()
  logging.debug(str((gts, pred)))
  if pred == gts: num_correct += 1
print ('By frame done in %.1f sec.' % (time() - start), end='')
print ('Out of %d, have %d correct' % ((iframe+1), num_correct))

