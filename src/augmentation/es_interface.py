import logging
import sys, os, os.path as op
import json
import ConfigParser
import traceback
from datetime import datetime
from elasticsearch import Elasticsearch, RequestsHttpConnection

# tracer = logging.getLogger('elasticsearch.trace')
# tracer.setLevel(logging.INFO)
# tracer.addHandler(logging.FileHandler('/tmp/es_trace.log'))

''' Interface with ElasticSearch database '''


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
    # logging.info ('config max time:            %f' % max_time)
    # logging.info ('config server_address:      %s' % server_address)
    # logging.info ('config server_credentials:  %s' % server_credentials)
    # logging.info ('config machine_name:        %s' % machine_name)
    return max_time, server_address, server_credentials, machine_name



class CAD_ES_interface:
    index_name = 'cad'
    type_name  = 'model'
    config_section = '3dmodel'

    def check_connection (self):
        ''' prints some info about the ES server '''
        return self.es.info()


    def __init__ (self, 
                  config_file='etc/monitor.ini', 
                  relpath=os.getenv('CITY_PATH'), 
                  cam_timezone='-05:00'):

        self.relpath = relpath
        self.cam_timezone = cam_timezone
        #self.verbose = args.verbose
        (self.max_time, self.server_address, self.server_credentials, self.machine_name) = \
            _read_config_file_ (config_file, self.config_section, self.relpath)

        creds = self.server_credentials.split(':')
        self.es = Elasticsearch(
            [self.server_address],
            connection_class=RequestsHttpConnection,
            http_auth=(creds[0], creds[1]),
        )


    def _get_hits_by_id_ (self, model_id):
        result = self.es.search(
            index=self.index_name,
            doc_type=self.type_name,
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
            index=self.index_name,
            doc_type=self.type_name,
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
            logging.info ('update_model_id: updating model')
            return self.es.index(
                index=self.index_name, 
                doc_type=self.type_name, 
                id=_id, 
                body=vehicle)
        # if insert
        else:
            logging.info ('update_model_id: inserting model')
            return self.es.index(
                index=self.index_name, 
                doc_type=self.type_name, 
                body=vehicle)


    def upload_collection_to_db (self, collection):
        for vehicle in collection['vehicles']:
            self.update_model (vehicle, collection['collection_id'])





class Camera_ES_interface:
    ''' nyc cameras '''
    index_name = 'cameras'
    type_name  = 'model'
    config_section = '3dmodel'

    def check_connection (self):
        ''' prints some info about the ES server '''
        return self.es.info()


    def __init__ (self, 
                  config_file='etc/monitor.ini', 
                  relpath=os.getenv('CITY_PATH'), 
                  cam_timezone='-05:00'):

        self.relpath = relpath
        self.cam_timezone = cam_timezone
        #self.verbose = args.verbose
        (self.max_time, self.server_address, self.server_credentials, self.machine_name) = \
            _read_config_file_ (config_file, self.config_section, self.relpath)

        creds = self.server_credentials.split(':')
        self.es = Elasticsearch(
            [self.server_address],
            connection_class=RequestsHttpConnection,
            http_auth=(creds[0], creds[1]),
        )


    def create_index(self):
        return self.es.indices.create(
            index=self.index_name, 
            ignore=400, 
            body={
                'mappings': {
                    '%s' % self.type_name:
                    {
                        'properties': {
                            'date': {
                                'type':   'date',
                                'format': 'yyyy-MM-dd HH:mm:ss.SSSZ'
                            },
                            'cam_id':   {'type': 'integer'},
                            'location': {'type': 'string',
                                         'index': 'not_analyzed' },
                            'pin': { 'type' : 'geo_point' }
                        }
                    }
                }
            }
            )


    def _get_hit_by_camid_ (self, cam_id):
        result = self.es.search(
            index=self.index_name,
            doc_type=self.type_name,
            ignore=400, 
            body = {
                      'query': {
                        'term': {
                          'cam_id': '%s' % cam_id 
                        }
                      }
                   }
            )
        if 'hits' not in result:
            return None
        hits = result['hits']['hits']
        assert len(hits) in [0, 1]
        if len(hits) == 0:
            return None
        elif len(hits) == 1:
            return hits[0]


    def update_camera (self, camera):
        '''Update entry.
        Args:
          camera - a dict
        '''
        # add some fields to vehicle
        timestr = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        camera['date'] = timestr + self.cam_timezone
        logging.debug (json.dumps(camera, indent=4))

        hit = self._get_hit_by_camid_ (camera['cam_id'])
        logging.debug('_get_hit_by_camid_ returned: %s' % json.dumps(hit, indent=4))

        # if update
        if hit: 
            _id = hit['_id']
            logging.info ('update_camera: updating camera')
            return self.es.index(
                index=self.index_name, 
                doc_type=self.type_name, 
                ignore=400, 
                id=_id, 
                body=camera)
        # if insert
        else:
            logging.info ('update_camera: inserting model')
            return self.es.index(
                index=self.index_name, 
                doc_type=self.type_name, 
                ignore=400, 
                body=camera)


    def delete_camera (self, cam_id):
        '''Delete camera.
        Args:
          camera - a dict
        '''
        hit = self._get_hit_by_camid_ (cam_id)
        logging.debug('_get_hit_by_camid_ returned: %s' % json.dumps(hit, indent=4))

        if not hit: 
            logging.error('did not find cam_id=%d to delete' % cam_id)
        else:
            _id = hit['_id']
            return self.es.delete(
                index=self.index_name, 
                doc_type=self.type_name, 
                ignore=400, 
                id=_id
            )

        








if __name__ == "__main__":
    logging.basicConfig (level=logging.INFO)

    #cad_db = CAD_ES_interface()
    #result = cad_db.check_connection()
    #result = cad_db._get_models_by_id_('test')
    #result = cad_db.get_model_by_id_and_collection (model_id='test', collection_id='test')
    #result = cad_db.update_model ({'model_id': 'test'}, collection_id='test')

    cam_db = Camera_ES_interface()
    result = cam_db.create_index()

    print json.dumps(result, indent=4)
    
