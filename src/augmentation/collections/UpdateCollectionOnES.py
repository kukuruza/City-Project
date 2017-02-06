import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import simplejson as json
import argparse
import logging
import shutil
from augmentation.Cad import Cad
from learning.helperSetup import setupLogging, atcity


parser = argparse.ArgumentParser()
parser.add_argument('--collection_id')
parser.add_argument('--logging_level', type=int, default=20)
args = parser.parse_args()

setupLogging('log/augmentation/UpdateCollection.log', args.logging_level, 'w')

collection_file = 'augmentation/CAD/%s/readme-blended.json' % args.collection_id
collection = json.load(open(atcity(collection_file)))

cad = Cad()

cad.update_collection (collection)
