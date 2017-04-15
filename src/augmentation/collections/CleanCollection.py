#!/usr/bin/env python
import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import json
import argparse
import logging
import subprocess
import shutil
import cv2
import traceback
from learning.helperSetup import setupLogging, atcity
from learning.helperSetup import setParamUnlessThere, assertParamIsThere
from learning.helperKeys import KeyReaderUser, getCalibration
from augmentation.Cad import Cad


WORK_DIR = atcity('data/augmentation/blender/current-collection')


class Diapason:

    def _parse_range_str_ (self, range_str, length):
        '''Parses python range STRING into python range
        '''
        assert isinstance(range_str, basestring)
        # remove [ ] around the range
        if len(range_str) >= 2 and range_str[0] == '[' and range_str[-1] == ']':
            range_str = range_str[1:-1]
        # split into three elements start,end,step. Assign step=1 if missing
        arr = range_str.split(':')
        assert len(arr) == 2 or len(arr) == 3, 'need 1 or 2 commas "," in range string'
        if len(arr) == 2: arr.append('1')
        if arr[0] == '': arr[0] = '0'
        if arr[1] == '': arr[1] = str(length)
        if arr[2] == '': arr[2] = '1'
        start = int(arr[0])
        end   = int(arr[1])
        step  = int(arr[2])
        range_py = range(start, end, step)
        logging.debug ('Diapason parsed range_str %s into range of length %d' % (range_str, len(range_py)))
        return range_py

    def get_range (self, length, range_str):
        return self._parse_range_str_ (range_str, length)



def clean_model (model, params={}):
    setParamUnlessThere (params, 'show_examples', False)

    collection_id = model['collection_id']
    model_id      = model['model_id']

    collection_dir = 'data/augmentation/CAD/%s' % collection_id
    
    # did we export .blend or .obj from .skp
    src_blend_file = op.join(collection_dir, 'blend_src/%s.blend' % model_id)
    src_obj_file   = op.join(collection_dir, 'obj/%s.obj' % model_id)
    if op.exists(atcity(src_blend_file)): 
        model['src_blend_file'] = src_blend_file
        logging.debug ('src_blend_file: %s' % src_blend_file)
    elif op.exists(atcity(src_obj_file)): 
        model['src_obj_file'] = src_obj_file
        logging.debug ('src_obj_file:   %s' % src_obj_file)
    else:
        logging.warning ('model %s was not converted from .skp' % model_id)
        model['error'] = "model was not converted from .skp, probably bad model"
        model['valid'] = False
        model['ready'] = False
        return model

    # where to save the result
    dst_blend_file   = op.join(collection_dir, 'blend/%s.blend' % model_id)
    dst_example_file = op.join(collection_dir, 'examples/%s.png' % model_id)
    model['dst_blend_file'] = dst_blend_file
    model['example_file']   = dst_example_file

    # write the model json file for cleanCollectionBlender
    src_model_path = op.join(WORK_DIR, 'model-src.json')
    with open(src_model_path, 'w') as f:
        f.write(json.dumps(model, indent=4))

    # delete for seeing blender failures
    dst_model_path = op.join(WORK_DIR, 'model-dst.json')
    if op.exists(dst_model_path):   os.remove(dst_model_path)

    try:
        command = ['%s/blender' % os.getenv('BLENDER_ROOT'), '--background', '--python',
                   atcity('src/augmentation/collections/cleanCollectionBlender.py')]
        returncode = subprocess.call (command, shell=False)
        logging.info ('blender returned code %s' % str(returncode))
    except:
        logging.error('failed: %s' % traceback.format_exc())

    model = json.load(open(dst_model_path))
    del model['dst_blend_file']
    del model['example_file']
    if 'src_blend_file' in model: del model['src_blend_file']
    if 'src_obj_file'   in model: del model['src_obj_file']

    # show example
    if model['valid']:
      example = cv2.imread(atcity(dst_example_file))
      assert example is not None, 'example was not written to %s' % dst_example_file
      if params['show_examples']:
          cv2.imshow('example', example)
          cv2.waitKey(-1)

    return model



parser = argparse.ArgumentParser()
parser.add_argument('--collection_id')
parser.add_argument('--model_range', default='[::]')
parser.add_argument('--show_examples', action='store_true')
parser.add_argument('--logging_level', type=int, default=20)
args = parser.parse_args()

setupLogging('log/augmentation/CleanBlender.log', args.logging_level, 'w')

src_collection_file = 'data/augmentation/CAD/%s/readme-src.json' % args.collection_id
collection = json.load(open(atcity(src_collection_file)))

logging.info ('found %d models in the collection' % len(collection['vehicles']))

for i in Diapason().get_range(len(collection['vehicles']), args.model_range):
    logging.debug ('model #%d' % i)
    model = collection['vehicles'][i]
    model['collection_id'] = args.collection_id
    model = clean_model (model, {'show_examples': args.show_examples})
    assert model is not None
    del model['collection_id']
    collection['vehicles'][i] = model

dst_collection_file = 'data/augmentation/CAD/%s/readme-blended.json' % args.collection_id
with open(atcity(dst_collection_file), 'w') as f:
    f.write(json.dumps(collection, indent=4))


# cad = Cad()
#
# update models
# collection_path = op.join(collection_dir, 'readme-blended.json')
# collection = json.load(open(collection_path))
# for model in collection['vehicles']:
#     cad.update_model (model, args.collection_id)
# with open(collection_path, 'w') as f:
#     f.write(json.dumps(collection, indent=4))
