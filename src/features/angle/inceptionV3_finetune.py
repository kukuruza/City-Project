#! /usr/bin/env python
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import argparse
import logging
import numpy as np
import tensorflow as tf
from keras.applications.inception_v3 import InceptionV3
from keras.applications.inception_v3 import preprocess_input
from keras.preprocessing import image
from keras.models import Model
from keras.layers import Dense, GlobalAveragePooling2D
from keras import backend as K
from keras.optimizers import SGD
from scipy.misc import imresize
from db.lib.dbDataset import CitycarsDataset
from dataset_utilities import *

parser = argparse.ArgumentParser()
parser.add_argument('--train_db_file', required=True)
parser.add_argument('--valid_db_files', nargs='*')
parser.add_argument('--out_h5_file')
parser.add_argument('--num_epochs', default=1, type=int)
parser.add_argument('--steps_per_epoch', default=10, type=int)
parser.add_argument('--batchsize', default=128, type=int)
parser.add_argument('--logging', default=20, type=int)
parser.add_argument('--show_layers', action='store_true')
args = parser.parse_args()

logging.basicConfig(level=args.logging)

dataset_train = CitycarsDataset(args.train_db_file, fraction=1.,
    crop_car=False, randomly=True, car_constraint='yaw IS NOT NULL')
datasets_valid = []
for valid_db_file in args.valid_db_files:
  datasets_valid.append( CitycarsDataset(valid_db_file, fraction=1.,
      crop_car=False, randomly=True, car_constraint='yaw IS NOT NULL') )

batchsize=args.batchsize

# create the base pre-trained model
base_model = InceptionV3(weights='imagenet', include_top=False, input_shape=(139,139,3))

# add a global spatial average pooling layer
x = base_model.output
x = GlobalAveragePooling2D()(x)
# let's add a fully-connected layer
x = Dense(1024, activation='relu')(x)
# and a logistic layer -- let's say we have 200 classes
predictions = Dense(12, activation='softmax')(x)

# this is the model we will train
model = Model(inputs=base_model.input, outputs=predictions)

# first: train only the top layers (which were randomly initialized)
# i.e. freeze all convolutional InceptionV3 layers
for layer in base_model.layers:
    layer.trainable = False

# compile the model (should be done *after* setting layers to non-trainable)
model.compile(optimizer='rmsprop', 
              loss='categorical_crossentropy',
              metrics=['categorical_accuracy'])

# train the model on the new data for a few epochs
print ('Fine-tuning all layers...')
for epoch in range(args.num_epochs):
  model.fit_generator(generate_batches(dataset_train, batchsize, blur=True, crop=True), 
      steps_per_epoch=args.steps_per_epoch, epochs=1)
  scores = model.evaluate_generator(iter(
    BatchGenerator(dataset_train, batchsize)), len(dataset_train) // batchsize)
  print ('dataset_train', model.metrics_names[1], scores[1])
  for dataset_valid in datasets_valid:
    scores = model.evaluate_generator(iter(
      BatchGenerator(dataset_valid, batchsize)), len(dataset_valid) // batchsize)
    print ('dataset_valid', model.metrics_names[1], '%.2f' % scores[1])


# at this point, the top layers are well trained and we can start fine-tuning
# convolutional layers from inception V3. We will freeze the bottom N layers
# and train the remaining top layers.

# let's visualize layer names and layer indices to see how many layers
# we should freeze:
if args.show_layers:
  for i, layer in enumerate(base_model.layers):
    print(i, layer.name)

# we chose to train the top 2 inception blocks, i.e. we will freeze
# the first 249 layers and unfreeze the rest:
for layer in model.layers[:249]:
   layer.trainable = False
for layer in model.layers[249:]:
   layer.trainable = True

# we need to recompile the model for these modifications to take effect
# we use SGD with a low learning rate
model.compile(optimizer=SGD(lr=0.0001, momentum=0.9),
              loss='categorical_crossentropy',
              metrics=['categorical_accuracy'])

# we train our model again (this time fine-tuning the top 2 inception blocks
# alongside the top Dense layers
print ('Fine-tuning top layers...')
for epoch in range(args.num_epochs):
  model.fit_generator(generate_batches(dataset_train, batchsize, blur=True, crop=True), 
      steps_per_epoch=args.steps_per_epoch, epochs=1)
  scores = model.evaluate_generator(iter(
    BatchGenerator(dataset_train, batchsize)), len(dataset_train) // batchsize)
  print ('dataset_train', model.metrics_names[1], '%.2f' % scores[1])
  for dataset_valid in datasets_valid:
    scores = model.evaluate_generator(iter(
      BatchGenerator(dataset_valid, batchsize)), len(dataset_valid) // batchsize)
    print ('dataset_valid', model.metrics_names[1], '%.2f' % scores[1])

if args.out_h5_file:
  model.save(args.out_h5_file)

