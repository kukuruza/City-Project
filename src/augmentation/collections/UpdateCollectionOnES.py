import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import simplejson as json
import argparse
import logging
import shutil
from augmentation.Cad import Cad
from learning.helperSetup import setupLogging, atcity


def update_collection (collection):
  cad = Cad()
  for model in collection['vehicles']:
    if model['ready']:
      cad.update_model (model, collection)


parser = argparse.ArgumentParser()
parser.add_argument('--collection_id')
parser.add_argument('--logging_level', type=int, default=20)
args = parser.parse_args()

setupLogging('log/augmentation/UpdateCollection.log', args.logging_level, 'w')

collection_file = 'data/augmentation/CAD/%s/collection.json' % args.collection_id
collection = json.load(open(atcity(collection_file)))

update_collection (collection)
