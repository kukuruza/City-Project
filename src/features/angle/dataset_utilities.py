#! /usr/bin/env python
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
from time import time
import numpy as np
import tensorflow as tf
from keras.applications.inception_v3 import preprocess_input
from scipy.misc import imresize
from db.lib.dbDataset import CitycarsDataset
from db.lib.helperDb import carField

def random_crop(image, (dy,dx)):
  height, width = image.shape[0:2]
  if width < dx or height < dy:
    return None
  x = np.random.randint(0, width - dx + 1)
  y = np.random.randint(0, height - dy + 1)
  return image[y:(y+dy), x:(x+dx), :]

def car_to_angle(car_entry):
  angle = int(carField(car_entry, 'yaw'))
  angle = angle // (360 // 12)
  return angle

def angle_to_one_hot(label, blur=False):
  label_one_hot = np.zeros([12], dtype=float)
  if blur:
    label_one_hot[label] = 0.6
    label_one_hot[(label + 1) % 12] = 0.2
    label_one_hot[(label - 1) % 12] = 0.2
  else:
    label_one_hot[label] = 1.
  return label_one_hot

def one_hot_to_angle(one_hot):
  angle = one_hot.argmax() * (360 // 12)
  return angle

def generate_batches(dataset, batchsize, blur=False, crop=False):
  batch = None
  while True:
    for i, (image, car_entry) in enumerate(dataset.__getitem__()):
      image = random_crop(image, (124,124))
      image = imresize(image, (139,139))
      image = image.astype(float)
      image = preprocess_input(image)
      label = car_to_angle(car_entry)
      label = angle_to_one_hot(label, blur=blur)
      if batch is None:
        batch = np.zeros([batchsize] + list(image.shape), dtype=float)
        labels = np.zeros([batchsize, 12], dtype=float)
      batch[i % batchsize] = image
      labels[i % batchsize] = label
      if (i+1) % batchsize == 0:
        #batch = preprocess_input(batch)
        yield batch, labels

class BatchGenerator:
  def __init__(self, dataset, batchsize, blur=False, crop=False):
    self.dataset = dataset
    self.batchsize = batchsize
    self.blur = blur
    self.crop=crop
  def __iter__(self):
    batch = None
    while True:
      for i, (image, car_entry) in enumerate(self.dataset.__getitem__()):
        image = random_crop(image, (124,124))
        image = imresize(image, (139,139))
        image = image.astype(float)
        image = preprocess_input(image)
        label = car_to_angle(car_entry)
        logging.debug(label)
        label = angle_to_one_hot(label, blur=self.blur)
        if batch is None:
          batch = np.zeros([self.batchsize] + list(image.shape), dtype=float)
          labels = np.zeros([self.batchsize, 12], dtype=float)
        batch[i % self.batchsize] = image
        labels[i % self.batchsize] = label
        if (i+1) % self.batchsize == 0:
          logging.debug(str(batch.shape))
          yield batch, labels


