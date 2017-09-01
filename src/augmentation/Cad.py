import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import logging
import simplejson as json
from pprint import pprint, pformat
import ConfigParser
import traceback
from datetime import datetime
from elasticsearch import Elasticsearch, RequestsHttpConnection
from learning.helperSetup import atcity, setupLogging

README_NAME = 'readme-blended.json'


def _read_config_file_ (config_file, section, relpath):
    config_path = op.join(relpath, config_file)
    assert op.exists(config_path)

    # try to read keys from the file
    config = ConfigParser.ConfigParser()
    config.read(config_path)

    max_time           = float(config.get(section, 'max_time'))
    server_address     = config.get(section, 'server_address')
    server_credentials = config.get(section, 'server_credentials')
    machine_name       = config.get(section, 'machine_name')
    logging.info ('config max time:            %f' % max_time)
    logging.info ('config server_address:      %s' % server_address)
    logging.info ('config server_credentials:  %s' % server_credentials)
    logging.info ('config machine_name:        %s' % machine_name)
    return max_time, server_address, server_credentials, machine_name



class Cad:
  '''CAD collections'''

  index_name = 'cad'
  type_name  = 'model'
  config_section = '3dmodel'

  def check_connection (self):
    ''' prints some info about the ES server '''
    return self.es.info()


  def _is_vehicle_type (self, vehicle_type=None):
    if vehicle_type is None:
      return {}
    else:
      return \
        {
          "term": {
            "vehicle_type": vehicle_type
          }
        }

  def _is_in_collection(self, collection_id=None):
    if collection_id is None:
      return {}
    else:
      return \
        {
          "term": {
            "collection_id": collection_id
          }
        }

  def _is_model(self, model_id):
    return \
      {
        "term": {
          "model_id": model_id
        }
      }

  def _is_ready (self):
    return \
      {
        'term': {
          'ready': True
        }
      }

  def _is_valid (self):
    return \
      {
        'term': {
          'valid': True
        }
      }


  def __init__ (self, 
                config_file='etc/monitor.ini', 
                cam_timezone='-05:00'):

      es_logger = logging.getLogger('elasticsearch')
      es_logger.setLevel(logging.WARNING)

      self.cam_timezone = cam_timezone
      #self.verbose = args.verbose
      (self.max_time, self.server_address, self.server_credentials, self.machine_name) = \
          _read_config_file_ (config_file, self.config_section, os.getenv('CITY_PATH'))

      creds = self.server_credentials.split(':')
      self.es = Elasticsearch(
          [self.server_address],
          connection_class=RequestsHttpConnection,
          http_auth=(creds[0], creds[1]),
          timeout=30,
          max_retries=10, 
          retry_on_timeout=True
      )


  def _get_hits_by_id_ (self, model_id):
      result = self.es.search(
          index=self.index_name,
          doc_type=self.type_name,
          body = {
                   "query": {
                     "term": {
                       "model_id": model_id 
                     }
                   }
                 }
          )
      hits = result['hits']['hits']
      return hits


  def _get_models_by_id_ (self, model_id):
      ''' get _source field from hits '''
      hits = self._get_hits_by_id_ (model_id)
      return [hit['_source'] for hit in hits]


  def get_hit_by_id_and_collection (self, model_id, collection_id):
    '''Find a model in ES, if any (result should be unique)
    While (model_id, collection_id) combination is unique,
      other collections may have the same model_id, but tagged invalid.
    '''
    body = {
      "query": {
        "bool": {
          "must": [
            self._is_model(model_id),
            self._is_in_collection(collection_id)
          ]
        }
      }
    }
    logging.debug ('get_hit_by_id_and_collection: %s' % pformat(body, indent=2))
    result = self.es.search(
        index=self.index_name,
        doc_type=self.type_name,
        body=body
    )
    hits = result['hits']['hits']
    assert len(hits) in [0, 1]
    if not hits:
        return None
    else:
        return hits[0]


  def get_model_by_id_and_collection (self, model_id, collection_id):
      ''' get _source field from hit '''
      hit = self.get_hit_by_id_and_collection (model_id, collection_id)
      return hit['_source'] if hit else None


  def get_ready_models (self, vehicle_type=None, collection_id=None):
    ''' get _source fields from all hits '''
    body = {
      "size": 10000,
      "query": {
        "bool": {
          "must": [
            self._is_ready(),
            self._is_valid(),
            self._is_vehicle_type(vehicle_type),
            self._is_in_collection(collection_id)
          ]
        }
      }
    }
    logging.debug ('get_ready_models: %s' % pformat(body, indent=2))
    result = self.es.search(
        index=self.index_name,
        doc_type=self.type_name,
        body=body
    )
    hits = result['hits']['hits']
    logging.info ('get_ready_models: got %d hits' % len(hits))
    return [hit['_source'] for hit in hits]



  def get_random_ready_models (self, vehicle_type=None, collection_id=None, number=1):
    body = {
      "size": number,
      "query": {
        "function_score": {
          "functions": [
            {
              "random_score" : {}
            }
          ],
          "score_mode": "sum",
          "query": {
            "bool": {
              "must": [
                  self._is_ready(),
                  self._is_valid(),
                  self._is_vehicle_type(vehicle_type),
                  self._is_in_collection(collection_id)
              ]
            }
          }
        }
      }
    }
    logging.debug ('get_random_ready_models: %s' % pformat(body, indent=2))
    result = self.es.search(
        index=self.index_name,
        doc_type=self.type_name,
        body=body)
    hits = result['hits']['hits']
    return [hit['_source'] for hit in hits]



  def is_model_in_other_collections (self, model_id, collection_id):
      ''' check if this model is known as a part of some other collection '''
      seen_models = self._get_models_by_id_ (model_id)
      #print json.dumps(seen_models, indent=4)

      # collect unique collection_ids, different from our current one
      seen_collection_ids = set()
      for seen_model in seen_models:
          if seen_model['collection_id'] != collection_id:
              seen_collection_ids.add (seen_model['collection_id'])
      seen_collection_ids = list(seen_collection_ids)

      return seen_collection_ids



  def update_model (self, model, collection):
      assert 'model_id' in model
      assert 'ready' in model and 'valid' in model 

      # add some fields to model
      model['author_name']     = collection['author_name']
      model['author_id']       = collection['author_id']
      model['collection_name'] = collection['collection_name']
      model['collection_id']   = collection['collection_id']
      if 'date' not in model:
          timestr = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
          model['date'] = timestr + self.cam_timezone
      logging.debug (json.dumps(model, indent=4))

      hit = self.get_hit_by_id_and_collection (
          model['model_id'], collection['collection_id'])
      logging.debug(json.dumps(hit, indent=4))

      # if update
      if hit: 
          _id = hit['_id']
          logging.info ('update_model_id: updating model')
          return self.es.index(
              index=self.index_name, 
              doc_type=self.type_name, 
              id=_id, 
              body=model)
      # if insert
      else:
          logging.info ('update_model_id: inserting model')
          return self.es.index(
              index=self.index_name, 
              doc_type=self.type_name, 
              body=model)






if __name__ == "__main__":
  logging.basicConfig (level=logging.DEBUG)

  cad = Cad()
  print cad.check_connection()
  #result = cad.get_model_by_id_and_collection (model_id='test', collection_id='test')
  #result = cad.update_model ({'model_id': 'test'}, collection_id='test')

  #result = cad.get_model_by_id_and_collection (model_id='test', collection_id='test')
  #result = cad.update_model ({'model_id': 'test'}, collection_id='test')

  # from glob import glob
  # for collection_dir in glob(atcity('data/augmentation/CAD/*')):
  #     if not op.isdir(collection_dir): continue
  #     for blend1_path in glob(op.join(collection_dir, 'blend/*.blend1')):
  #         os.remove (blend1_path)
  #     for blend1_path in glob(op.join(collection_dir, 'blend_src/*.blend1')):
  #         os.remove (blend1_path)

      # if not op.isdir(collection_dir): continue
      # collection_path = op.join(collection_dir, 'readme-blended.json')
      # if not op.exists(collection_path): continue
      # collection = json.load(open(collection_path))
      # update_collection(collection)

  #collection_path = atcity('data/augmentation/CAD/5f08583b1f45a9a7c7193c87bbfa9088/readme-blended.json')
  #collection = json.load(open(collection_path))
  #cad.update_collection(collection)

  collection_id = '5f08583b1f45a9a7c7193c87bbfa9088'
  models = cad.get_ready_models (collection_id=collection_id)
  # for model in models:
  #     assert 'ready' in model
  # print (json.dumps(models, indent=4))
  print len(models)
