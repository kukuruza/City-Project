#! /usr/bin/env python
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))

import argparse
from keras.applications.resnet50 import ResNet50
from keras.preprocessing import image
from keras.applications.resnet50 import preprocess_input, decode_predictions
import numpy as np
from scipy.misc import imresize
from db.lib.dbDataset import CityimagesDataset

parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
args = parser.parse_args()

dataset = CityimagesDataset(args.in_db_file, fraction=0.1)

model = ResNet50(weights='imagenet')

for img in dataset.iterateImages(randomly=True):
  #img = image.load_img(img_path, target_size=(224, 224))
  img = imresize(img, (224,224))
  x = image.img_to_array(img)
  x = np.expand_dims(x, axis=0)
  x = preprocess_input(x)

  preds = model.predict(x)
  # decode the results into a list of tuples (class, description, probability)
  # (one such list for each sample in the batch)
  print('Predicted:', decode_predictions(preds, top=3)[0])
  # Predicted: [(u'n02504013', u'Indian_elephant', 0.82658225), (u'n01871265', u'tusker', 0.1122357), (u'n02504458', u'African_elephant', 0.061040461)]
