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
from db.lib.helperDb import carField

np.set_printoptions(precision=2, linewidth=120, suppress=True)

parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--out_h5_file')
parser.add_argument('--num_epochs', default=1, type=int)
parser.add_argument('--steps_per_epoch', default=10, type=int)
parser.add_argument('--logging_level', default=20, type=int)
parser.add_argument('--show_layers', action='store_true')
args = parser.parse_args()

#logging.basicConfig(level=args.logging_level)

# Setting crop_car to False since we want the full patch.
dataset = CitycarsDataset(args.in_db_file, fraction=1., crop_car=False, randomly=False)

def car_to_label(car_entry, blur):
  label = int(carField(car_entry, 'yaw'))
  label = label // (360 // 12)
  label_one_hot = np.zeros([12], dtype=float)
  if blur:
    label_one_hot[label] = 0.6
    label_one_hot[(label + 1) % 12] = 0.2
    label_one_hot[(label - 1) % 12] = 0.2
  else:
    label_one_hot[label] = 1.
  return label_one_hot

def generate_batches(dataset, batchsize, blur=False):
  batch = None
  while True:
    for i, (image, car_entry) in enumerate(dataset.__getitem__()):
      image = imresize(image, (139,139))
      label = car_to_label(car_entry, blur=blur)
      if batch is None:
        batch = np.zeros([batchsize] + list(image.shape), dtype=float)
        labels = np.zeros([batchsize, 12], dtype=float)
      batch[i % batchsize] = image
      labels[i % batchsize] = label
      if (i-1) % batchsize == 0:
        batch = preprocess_input(batch)
        logging.debug((str(batch.shape), str(labels)))
        yield batch, labels
    

#for i, (batch,labels) in enumerate(generate_batches(dataset, 4)):
#  if i == 10: sys.exit()

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
model.fit_generator(generate_batches(dataset, 16, blur=True), 
    steps_per_epoch=args.steps_per_epoch, epochs=args.num_epochs)

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
model.fit_generator(generate_batches(dataset, 16, blur=False),
    steps_per_epoch=args.steps_per_epoch, epochs=args.num_epochs)

if args.out_h5_file:
  model.save(args.out_h5_file)
