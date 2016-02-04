import logging
import sys, os, os.path as op
import json
import argparse
import urllib2
import ConfigParser
import traceback
from datetime import datetime


'''CAD to ElasticSearch database interface'''


class CAD_ES_interface:

    def _read_config_file_ (self, config_file, relpath):
        config_path = op.join(relpath, config_file)
        assert op.exists(config_path)

        # try to read keys from the file
        config = ConfigParser.ConfigParser()
        config.read(config_path)

        self.max_time           = float(config.get('3dmodel_CAD_local', 'max_time'))
        self.server_address     = config.get('3dmodel_CAD_local', 'server_address')
        self.server_credentials = config.get('3dmodel_CAD_local', 'server_credentials')
        self.machine_name       = config.get('3dmodel_CAD_local', 'machine_name')
        logging.info ('config max time:            %f' % self.max_time)
        logging.info ('config server_address:      %s' % self.server_address)
        logging.info ('config server_credentials:  %s' % self.server_credentials)
        logging.info ('config machine_name:        %s' % self.machine_name)


    def __init__ (self, config_file='etc/monitor.ini', relpath=os.getenv('CITY_PATH')):

        self.relpath = relpath
        #self.verbose = args.verbose
        self._read_config_file_ (config_file, self.relpath)


    def _get_models_by_id_ (self, model_id):
        query =  '''{
                      "query": {
                        "term": {
                          "model_id": "%s" 
                        }
                      }
                    }
                ''' % model_id

        request = urllib2.Request (self.server_address + '/cad/model/_search', query)
        f = urllib2.urlopen(request)
        response = json.loads(f.read())
        f.close()
        logging.debug ('_get_models_by_id_ response: %s' % response)

        hits = response['hits']['hits']
        vehicles = [hit['_source'] for hit in hits]
        return vehicles


    def get_model_by_id_and_collection (self, model_id, collection_id):
        '''Find a model in ES, if any (result should be unique)
        '''
        query =  '''{ 
                      "query": {
                        "bool": {
                          "must": [
                            {
                              "term": {
                                "model_id": "%s"
                              }
                            },
                            {
                              "term": {
                                "collection_id": "%s"
                              }
                            }
                          ]
                        }
                      }
                    }
                ''' % (model_id, collection_id)
        request = urllib2.Request (self.server_address + '/cad/model/_search', query)
        f = urllib2.urlopen(request)
        response = json.loads(f.read())
        f.close()
        logging.debug ('get_model_by_id_and_collection response: %s' % response)
        hits = response['hits']['hits']
        assert len(hits) in [0, 1]
        if not hits:
            return None
        else:
            return hits[0]['_source']


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


    def update_model (self, vehicle, collection_id):
        assert 'model_id' in vehicle

        # add some fields to vehicle
        timestr = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        vehicle['date'] = timestr
        vehicle['collection_id'] = collection_id
        logging.debug (json.dumps(vehicle, indent=4))

        # find (model_id, collection_id) in ES, if any
        query =  '''{ 
                      "query": {
                        "bool": {
                          "must": [
                            {
                              "term": {
                                "model_id": "%s"
                              }
                            },
                            {
                              "term": {
                                "collection_id": "%s"
                              }
                            }
                          ]
                        }
                      }
                    }
                ''' % (vehicle['model_id'], collection_id)
        request = urllib2.Request (self.server_address + '/cad/model/_search', query)
        f = urllib2.urlopen(request)
        response = json.loads(f.read())
        f.close()
        logging.debug ('update_model: 1st response: %s' % response)
        hits = response['hits']['hits']
        assert len(hits) in [0, 1]

        # if update
        if hits: 
            _id = hits[0]['_id']
            logging.warning ('update_model_id: updating model')
            request = urllib2.Request (self.server_address + '/cad/model/%s' % _id, 
                                       json.dumps(vehicle))
        # if insert
        else:
            logging.info ('update_model_id: inserting model')
            request = urllib2.Request (self.server_address + '/cad/model/', 
                                       json.dumps(vehicle))

        f = urllib2.urlopen(request)
        response = json.loads(f.read())
        f.close()
        logging.debug ('response: %s' % response)



    def upload_collection_to_db (self, collection):
        for vehicle in collection['vehicles']:
            self.update_model (vehicle, collection['collection_id'])





