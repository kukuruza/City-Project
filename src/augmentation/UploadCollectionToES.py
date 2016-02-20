import logging
import sys, os, os.path as op
import json
import argparse
import shutil
from Cad import Cad

sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
from helperSetup import atcity, setupLogging


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--collection_id')
    parser.add_argument('--readme_name', nargs='?', default='readme-blended.json')
    parser.add_argument('--logging_level', default=30, type=int)
    args = parser.parse_args()

    setupLogging('log/augmentation/UploadCollectionToES.log', args.logging_level, 'a')

    CAD_dir = op.join(os.getenv('CITY_DATA_PATH'), 'augmentation/CAD')

    collection_path = op.join(CAD_dir, args.collection_id, args.readme_name)
    assert op.exists(collection_path), '%s' % collection_path
    collection = json.load(open(collection_path))

    cad = Cad()
    cad.upload_collection_to_db (collection)

    #vehicles = cad.get_by_model_id ('ubf392cd5-07a5-41c7-8148-3f7a0dc4e296')
    #print json.dumps(vehicles, indent=4)

    #print cad.is_model_in_other_collections (model_id="ubf392cd5-07a5-41c7-8148-3f7a0dc4e296", 
    #                                     collection_id="ec20cadc5f597c1a18e1def0c8a19a56_OTHER")

    #cad.update_model ({'model_id': "123"}, "ec20cadc5f597c1a18e1def0c8a19a56")
