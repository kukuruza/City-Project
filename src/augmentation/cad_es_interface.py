import logging
import sys, os, os.path as op
import json
import ConfigParser
import traceback
from datetime import datetime
from elasticsearch import Elasticsearch, RequestsHttpConnection

tracer = logging.getLogger('elasticsearch.trace')
tracer.setLevel(logging.INFO)
tracer.addHandler(logging.FileHandler('/tmp/es_trace.log'))

'''CAD to ElasticSearch database interface'''


class CAD_ES_interface:

    def check_connection (self):
        ''' prints some info about the ES server '''
        return self.es.info()


    def _read_config_file_ (self, config_file, relpath):
        config_path = op.join(relpath, config_file)
        assert op.exists(config_path)

        # try to read keys from the file
        config = ConfigParser.ConfigParser()
        config.read(config_path)

        section = '3dmodel_CAD'
        self.max_time           = float(config.get(section, 'max_time'))
        self.server_address     = config.get(section, 'server_address')
        self.server_credentials = config.get(section, 'server_credentials')
        self.machine_name       = config.get(section, 'machine_name')
        logging.info ('config max time:            %f' % self.max_time)
        logging.info ('config server_address:      %s' % self.server_address)
        logging.info ('config server_credentials:  %s' % self.server_credentials)
        logging.info ('config machine_name:        %s' % self.machine_name)


    def __init__ (self, 
                  config_file='etc/monitor.ini', 
                  relpath=os.getenv('CITY_PATH'), 
                  cam_timezone='-05:00'):

        self.relpath = relpath
        self.cam_timezone = cam_timezone
        #self.verbose = args.verbose
        self._read_config_file_ (config_file, self.relpath)

        creds = self.server_credentials.split(':')
        self.es = Elasticsearch(
            [self.server_address],
            connection_class=RequestsHttpConnection,
            http_auth=(creds[0], creds[1]),
        )


    def _get_hits_by_id_ (self, model_id):
        result = self.es.search(
            index='cad',
            doc_type='model',
            body = {
                      'query': {
                        'term': {
                          'model_id': '%s' % model_id 
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
        '''
        result = self.es.search(
            index='cad',
            doc_type='model',
            body = {
                      'query': {
                        'bool': {
                          'must': [
                            {
                              'term': {
                                'model_id': '%s' % model_id
                              }
                            },
                            {
                              'term': {
                                'collection_id': '%s' % collection_id
                              }
                            }
                          ]
                        }
                      }
                   }
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
        vehicle['collection_id'] = collection_id
        if 'date' not in vehicle:
            timestr = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            vehicle['date'] = timestr + self.cam_timezone
        logging.debug (json.dumps(vehicle, indent=4))

        hit = self.get_hit_by_id_and_collection (vehicle['model_id'], collection_id)
        logging.debug(json.dumps(hit, indent=4))

        # if update
        if hit: 
            _id = hit['_id']
            logging.warning ('update_model_id: updating model')
            return self.es.index(
                index='cad', 
                doc_type='model', 
                id=_id, 
                body=vehicle)
        # if insert
        else:
            logging.info ('update_model_id: inserting model')
            return self.es.index(
                index='cad', 
                doc_type='model', 
                body=vehicle)



    def upload_collection_to_db (self, collection):
        for vehicle in collection['vehicles']:
            self.update_model (vehicle, collection['collection_id'])



if __name__ == "__main__":
    logging.basicConfig (level=logging.INFO)
    cad_db = CAD_ES_interface()
    #print cad_db.check_connection()
    #result = cad_db._get_models_by_id_('ubf392cd5-07a5-41c7-8148-3f7a0dc4e296')
    #result = cad_db.get_model_by_id_and_collection(
    #    model_id='ubf392cd5-07a5-41c7-8148-3f7a0dc4e296',
    #    collection_id='ec20cadc5f597c1a18e1def0c8a19a56')
    result = cad_db.update_model ({'model_id': 'test'}, collection_id='test')
    print json.dumps(result, indent=4)
    
