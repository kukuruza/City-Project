#! /usr/bin/env python
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import argparse
import logging
import numpy as np
import tensorflow as tf
from keras.preprocessing import image
from keras.models import Model
from keras.layers import Dense, GlobalAveragePooling2D
from keras import backend as K
from keras.optimizers import SGD, Adam
from keras.models import Sequential
from keras.layers import *
from scipy.misc import imresize
from db.lib.dbDataset import CitycarsDataset
from dataset_utilities import *

parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--num_epochs', default=1, type=int)
parser.add_argument('--steps_per_epoch', default=10, type=int)
parser.add_argument('--logging', default=20, type=int)
parser.add_argument('--out_h5_file', required=False)
args = parser.parse_args()

logging.basicConfig(level=args.logging)

batchsize = 16
dataset = CitycarsDataset(args.in_db_file, fraction=0.025, crop_car=False, randomly=False,
                          car_constraint='yaw IS NOT NULL')

input_shape = (139,139,3)
model = Sequential()

#y = [label2id[l] for l in labels.reshape(-1)]
#y =  keras.utils.to_categorical(y)

model.add(Conv2D(32, (5, 5), strides=(2,2), input_shape=input_shape))
model.add(Activation('relu'))
#model.add(BatchNormalization())

model.add(MaxPooling2D(pool_size=(2, 2)))
#model.add(BatchNormalization())
#model.add(Dropout(0.3))

model.add(Conv2D(64, (3, 3)))
model.add(Activation('relu'))
#model.add(BatchNormalization())
model.add(MaxPooling2D(pool_size=(2, 2)))
#model.add(BatchNormalization())
#model.add(Dropout(0.3))

model.add(Conv2D(512, (1, 1)))
model.add(Activation('relu'))
#model.add(BatchNormalization())
#model.add(Dropout(0.5))

model.add(Conv2D(15, (1, 1)))
model.add(Activation('relu'))
#model.add(BatchNormalization())

model.add(GlobalAveragePooling2D())

model.add(Dense(500, activation='relu'))
#model.add(Dropout(0.5))
model.add(Dense(12, activation='softmax'))

opt = Adam(lr=0.002, beta_1=0.9, beta_2=0.999, epsilon=1e-08)
#model.compile(loss='categorical_crossentropy', optimizer=opt, metrics=['accuracy'])

#model.fit(np.expand_dims(X, axis=3), y, batch_size=200, epochs=15, validation_data=(np.expand_dims(X_val,3), y_val))


# compile the model (should be done *after* setting layers to non-trainable)
model.compile(optimizer='rmsprop', 
              loss='categorical_crossentropy',
              metrics=['categorical_accuracy'])

# train the model on the new data for a few epochs
print ('Fine-tuning all layers...')
model.fit_generator(generate_batches(dataset, batchsize, blur=False), 
    steps_per_epoch=args.steps_per_epoch, epochs=args.num_epochs)

if args.out_h5_file:
  model.save(args.out_h5_file)

print ('Evaluating...')
scores = model.evaluate_generator(iter(
  BatchGenerator(dataset, batchsize)), len(dataset) // batchsize)
print (model.metrics_names[0], scores[0])
print (model.metrics_names[1], scores[1])

print ('Predicting by image...')
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
print ('Out of %d, have %d correct' % ((iframe+1), num_correct))

print ('Predicting by batch...')
num_correct = 0
for ibatch, (images, car_entries) in enumerate(dataset.get_batch((139,139), batchsize)):
  gts = np.array([car_to_angle(car_entry) for car_entry in car_entries])
  images = images.astype(float)
  images = preprocess_input(images)
  pred = model.predict_on_batch(images).argmax(axis=1)
  logging.debug(str(np.column_stack((gts, pred))))
  num_correct += np.count_nonzero(pred == gts)
  break
print ('Out of %d, have %d correct' % ((ibatch+1) * batchsize, num_correct))

