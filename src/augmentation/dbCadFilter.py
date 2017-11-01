import os, sys, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import numpy as np
import logging
from tqdm import tqdm
from pprint import pprint
from db.lib.helperDb import deleteCars, deleteCar, carField, imageField, doesTableExist
from db.lib.helperSetup import atcity
from augmentation.Cad import Cad


def add_parsers(subparsers):
  filterByCadCollectionsParser(subparsers)
  filterByCadTypesParser(subparsers)


def filterByCadCollectionsParser(subparsers):
  parser = subparsers.add_parser('filterByCadCollections',
    description='Keep or remove chosen collections, assuming "name" is model_id')
  parser.set_defaults(func=filterByCadCollections)
  group = parser.add_mutually_exclusive_group()
  group.add_argument('--keep_cad_collections', nargs='+')
  group.add_argument('--remove_cad_collections', nargs='+')

def filterByCadCollections (c, args):
  logging.info ('==== filterByCadCollections ====')
  has_polygons = doesTableExist(c, 'polygons')
  has_matches = doesTableExist(c, 'matches')

  cad = Cad()
  models = cad.get_ready_models()

  c.execute('SELECT * FROM cars')
  for car_entry in tqdm(c.fetchall()):
    car_id = carField(car_entry, 'id')
    name = carField(car_entry, 'name')
    # TODO: maybe speed optimize by requesting ES for each model.
    found = False
    for model in models:
      if name == str(model['model_id']):
        found = True
        break
    assert found, name

    collection_id = model['collection_id']
    if (args.keep_cad_collections and collection_id not in args.keep_cad_collections
      or args.remove_cad_collections and collection_id in args.remove_cad_collections):
        deleteCar (c, car_id, has_polygons=has_polygons, has_matches=has_matches)


def filterByCadTypesParser(subparsers):
  parser = subparsers.add_parser('filterByCadTypes',
    description='Keep or remove chosen cad types, assuming "name" is model_id')
  parser.set_defaults(func=filterByCadTypes)
  group = parser.add_mutually_exclusive_group()
  group.add_argument('--keep_cad_types', nargs='+')
  group.add_argument('--remove_cad_types', nargs='+')

def filterByCadTypes (c, args):
  logging.info ('==== filterByCadTypes ====')
  has_polygons = doesTableExist(c, 'polygons')
  has_matches = doesTableExist(c, 'matches')

  cad = Cad()
  models = cad.get_ready_models()

  c.execute('SELECT * FROM cars')
  for car_entry in tqdm(c.fetchall()):
    car_id = carField(car_entry, 'id')
    name = carField(car_entry, 'name')
    # TODO: maybe speed optimize by requesting ES for each model.
    found = False
    for model in models:
      if name == str(model['model_id']):
        found = True
        break
    assert found, name

    vehicle_type = model['vehicle_type']
    if (args.keep_cad_types and vehicle_type not in args.keep_cad_types
      or args.remove_cad_types and vehicle_type in args.remove_cad_types):
        deleteCar (c, car_id, has_polygons=has_polygons, has_matches=has_matches)


