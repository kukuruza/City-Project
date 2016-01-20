import bpy
import json
import os, os.path as op
import argparse


'''
Scale each model in a collection up or down
'''

def scaleCollection (collection_dir, sc):

    collection_info = json.load(open(op.join(collection_dir, '_collection_.json')))

    for vehicle in collection_info['vehicles']:

        valid = vehicle['valid'] if 'valid' in vehicle else True
        if not valid: continue

        collection_id = collection_info['collection_id']
        model_id = vehicle['model_id']

        obj_path = op.join(collection_dir, 'obj', '%s.obj' % model_id)
        dae_path = op.join(collection_dir, 'dae', '%s.dae' % model_id)

        bpy.ops.import_scene.obj (filepath=obj_path)

        bpy.ops.transform.resize (value=(sc, sc, sc))

        bpy.ops.wm.collada_export (filepath=dae_path, selected=True)

        bpy.ops.object.delete()


#if __name__ == "__main__":
#
#    parser = argparse.ArgumentParser()
#    parser.add_argument('--collection_path')
#    parser.add_argument('--scale')
#    args = parser.parse_args()
#
#    scaleCollection (args.collection_path, args.scale)

collection_dir = op.join(os.getenv('CITY_DATA_PATH'), 
    'augmentation/CAD/7c7c2b02ad5108fe5f9082491d52810')

scale = 1.08

scaleCollection (collection_dir, scale)
