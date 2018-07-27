import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import simplejson as json
import numpy as np
from argparse import ArgumentParser
import progressbar
import logging
import re
from db.lib.helperSetup import atcity
from collection_utilities import deleteAbsoleteFields, backupFile

'''
Get car make/year/model out of model name and description.
'''

def extractCarInfoParser():
  parser = ArgumentParser('Extract car make, model and year from the name and description.')
  parser.add_argument('--collection_id')
#  parser.add_argument('--fps', type=int, default=2)
#  parser.add_argument('--imwidth', type=int, required=True)
  return parser

def _cleanString(s):
  s = s.lower()
  s = re.sub('[-\/]', ' ', s)  # Replace -, / with space.
  s = re.sub('[^A-Za-z0-9 ]+', '', s)  # Remove special characters.
  return s

def _findNDigits(s, n):
  ''' Used to find years. Cases like '2345' are not filtered for simplicity. '''
  return [re.findall('\d{%d}' % n, match.group())[0] for match in
          re.finditer('(^|[^\w])\d{%d}($|[^\w])' % n, s)]
#          re.finditer('(^|[^0-9])\d{%d}($|[^0-9])' % n, s)]

def _parseString(s, carsdb):
  # Get years.
  myyears = _findNDigits(s, 4) + _findNDigits(s, 2)

  s = _cleanString(s)

  # Get car makes.
  mycarmakes = []
  for carmake in carsdb:
    if carmake in s:
      mycarmakes.append(carmake)
  # Get car models.
  mycarmodels = []
  if mycarmakes:
    for carmodel in carsdb[mycarmakes[0]]:
      if carmodel in s:
        mycarmodels.append(carmodel)
  return myyears, mycarmakes, mycarmodels

def extractCarInfo(args, collection):

  carsdb_raw = json.load(open('/Users/evg/projects/City-Project/data/augmentation/resources/car-list.json'))
  carsdb = {}
  for entry in carsdb_raw:
    carsdb[entry['brand'].lower()] = [x.lower() for x in entry['models']]

  n_parsed_years = 0
  n_parsed_makes = 0
  n_parsed_models = 0

  for vehicle in collection['vehicles']:
    deleteAbsoleteFields(vehicle)

    if 'model_name' not in vehicle:  # Bad models don't have it.
      continue

    model_name = vehicle['model_name']
    caryears, carmakes, carmodels = _parseString(model_name, carsdb)
  
    if not ('car_year' in vehicle and vehicle['car_year'] != ' '.join(caryears)):
      vehicle['car_year'] = ' '.join(caryears)
    if caryears:
      n_parsed_years += 1
      if len(caryears) > 1:
        logging.warning('Found multiple years in %s' % model_name)
    else:
      logging.debug('Failed to parse Year      in: %s' % model_name)

    if not ('car_make' in vehicle and vehicle['car_make']):
      vehicle['car_make'] = carmakes[0] if carmakes else ''
    if carmakes:
      n_parsed_makes += 1
      if len(carmakes) > 1:
        logging.warning('Found multiple makes in %s' % model_name)
    else:
      logging.debug('Failed to parse   Make    in: %s' % model_name)

    if not ('car_model' in vehicle and vehicle['car_model']):
      vehicle['car_model'] = carmodels[0] if carmodels else ''
    if carmodels:
      n_parsed_models += 1
      if len(carmodels) > 1:
        logging.warning('Found multiple models in %s' % model_name)
    else:
      logging.debug('Failed to parse     Model in: %s' % model_name)

  logging.info('Parsed %d years' % n_parsed_years)
  logging.info('Parsed %d makes' % n_parsed_makes)
  logging.info('Parsed %d models' % n_parsed_models)

if __name__ == '__main__':
  parser = extractCarInfoParser()
  parser.add_argument('--logging', default=20, type=int, choices={10, 20, 30, 40},
      help='Log debug (10), info (20), warning (30), error (40).')
  parser.add_argument('--dryrun', action='store_true',
      help='Do not write anything.')
  args = parser.parse_args()

  progressbar.streams.wrap_stderr()
  logging.basicConfig(level=args.logging, format='%(levelname)s: %(message)s')

  # Open the collection and vehicle information.
  collection_file = 'data/augmentation/CAD/%s/collection.json' % args.collection_id
  collection = json.load(open(atcity(collection_file)))
  logging.info('found %d models in the collection' % len(collection['vehicles']))

  extractCarInfo(args, collection)
  #_parseString('2010 Toyota 1987 2100 87 896 #Verso-S/Ractis (Low Poly)')

  # Parse and write.
  if not args.dryrun:
    backupFile(collection_file, collection_file)
    with open(atcity(collection_file), 'w') as f:
      f.write(json.dumps(collection, indent=2))
