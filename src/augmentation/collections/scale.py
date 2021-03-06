import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import json
import logging
import bpy
from augmentation.render.common import *
from augmentation.collections.collectionUtilities import WORK_DIR, atcity


def scaleModel (model_id, scale):
    obj = bpy.data.objects[model_id]
    obj.select = True
    bpy.ops.transform.resize (value=(scale, scale, scale))


if __name__ == '__main__':

    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

    model_path = op.join(WORK_DIR, 'model.json')
    model = json.load(open(model_path))

    scale = model['scale']
    logging.info('Will scale with f=%f' % scale)

    dry_run = model['dry_run']
    logging.info('Dry run mode is %s.' % ('on' if dry_run else 'off'))

    model_id = op.basename(op.splitext(model['blend_file'])[0])
    logging.info('Processing model: %s' % model_id)

    scene_path = atcity('data/augmentation/scenes/empty-import.blend')
    bpy.ops.wm.open_mainfile(filepath=atcity(model['blend_file']))

    logging.info('Import succeeded.')
    scaleModel (model_id, scale)
    status = 'ok'

    if not dry_run:
      bpy.ops.wm.save_as_mainfile(filepath=atcity(model['blend_file']))

    with open(model_path, 'w') as fid:
        fid.write(json.dumps({'status': status}, indent=2))
