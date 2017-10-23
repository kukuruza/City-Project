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
from keras.models import Model, load_model
from keras.layers import Dense, GlobalAveragePooling2D
from keras import backend as K
from keras.optimizers import SGD
from scipy.misc import imresize
from db.lib.dbDataset import CitycarsDataset
from db.lib.helperDb import carField

np.set_printoptions(precision=2, linewidth=120, suppress=True)

parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--in_h5_file', required=True)
parser.add_argument('--logging_level', default=20, type=int)
args = parser.parse_args()

logging.basicConfig(level=args.logging_level)

# Setting crop_car to False since we want the full patch.
dataset = CitycarsDataset(args.in_db_file, fraction=1., crop_car=False, randomly=True)

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
  return label_one_hot, label

def generate_batches(dataset, batchsize, blur=False):
  batch = None
  while True:
    for i, (image, car_entry) in enumerate(dataset.iterateImages()):
      image = imresize(image, (139,139))
      label, _ = car_to_label(car_entry, blur=blur)
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

model = load_model(args.in_h5_file)

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
              metrics=['top_k_categorical_accuracy'])

# we train our model again (this time fine-tuning the top 2 inception blocks
# alongside the top Dense layers
#print ('Fine-tuning top layers...')
#model.fit_generator(generate_batches(dataset, 16, blur=False),
#    steps_per_epoch=1, epochs=1)

print ('Evaluating...')
for images, labels in generate_batches(dataset, 1024):
  break
scores = model.evaluate(images, labels, verbose=1)

#scores = model.evaluate_generator(
#    generate_batches(dataset, 1), steps=1)#len(dataset) / 1024)
print (model.metrics_names[0], scores[0])
print (model.metrics_names[1], scores[1])

dataset = CitycarsDataset(args.in_db_file, fraction=1., crop_car=False, randomly=False)
for i, (img, car_entry) in enumerate(dataset.__getitem__()):
  img = imresize(img, (139,139))
  img = img.astype(float)
  img = preprocess_input(img)
  img = np.expand_dims(img, axis=0)

  preds = model.predict(img).argmax()
  print (preds, car_to_label(car_entry, blur=False)[1])
  if i == 32: sys.exit()

