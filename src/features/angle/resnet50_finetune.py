#! /usr/bin/env python
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))

import argparse
import logging
import numpy as np
import tensorflow as tf
from keras.applications.resnet50 import ResNet50
from keras.preprocessing import image
from keras.applications.resnet50 import preprocess_input, decode_predictions
from keras.models import Model
from keras.layers import Dense, GlobalAveragePooling2D
from keras import backend as K


from scipy.misc import imresize
from learning.data4tf.dbCityCars import CitycarsDataset
from learning.helperDb import carField

parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--logging_level', default=20, type=int)
args = parser.parse_args()

logging.basicConfig(level=args.logging_level)

# Setting crop_car to False since we want the full patch.
dataset = CitycarsDataset(args.in_db_file, fraction=0.1, crop_car=False)

def generate_batches(dataset, batchsize):
  batch = None
  while True:
    for i, (image, car_entry) in enumerate(dataset.iterateImages()):
      image = imresize(image, (224,224))
      image = image.astype(float)
      image = preprocess_input(image)
      label = carField(car_entry, 'yaw')
      label_one_hot = np.zeros([12], dtype=float)
      label_one_hot[int(label // (360 / 12))] = 1.
      if batch is None:
        batch = np.zeros([batchsize] + list(image.shape), dtype=float)
        labels = np.zeros([batchsize, 12], dtype=float)
      batch[i % batchsize] = image
      labels[i % batchsize] = label_one_hot
      if (i-1) % batchsize == 0:
        logging.debug((str(batch.shape), str(labels)))
        yield batch, labels
    

#for i, (batch,labels) in enumerate(generate_batches(dataset, 4)):
#  if i == 10: sys.exit()

# create the base pre-trained model
base_model = ResNet50(weights='imagenet', include_top=False)

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
model.compile(optimizer='rmsprop', loss='categorical_crossentropy')

# train the model on the new data for a few epochs
model.fit_generator(generate_batches(dataset, 16), steps_per_epoch=10, epochs=1)

# at this point, the top layers are well trained and we can start fine-tuning
# convolutional layers from inception V3. We will freeze the bottom N layers
# and train the remaining top layers.

# let's visualize layer names and layer indices to see how many layers
# we should freeze:
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
from keras.optimizers import SGD
model.compile(optimizer=SGD(lr=0.0001, momentum=0.9), loss='categorical_crossentropy')

# we train our model again (this time fine-tuning the top 2 inception blocks
# alongside the top Dense layers
model.fit_generator(generate_batches(dataset, 16), steps_per_epoch=10, epochs=1)

for img in dataset.iterateImages(randomly=True):
  #img = image.load_img(img_path, target_size=(224, 224))
  img = imresize(img, (224,224))
  x = image.img_to_array(img)
  x = np.expand_dims(x, axis=0)
  x = preprocess_input(x)

  preds = model.predict(x)
  # decode the results into a list of tuples (class, description, probability)
  # (one such list for each sample in the batch)
#  print('Predicted:', decode_predictions(preds, top=3)[0])
  print (preds)
