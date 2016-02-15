import logging
import sys, os, os.path as op
import json
import argparse
import shutil
import glob
from es_interface import Camera_ES_interface

def atcity(x):
    op.join(os.getenv('CITY_DATA_PATH'), x)

sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
from helperSetup import atcity, setupLogging


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--delete', action='store_true')
    parser.add_argument('--cam_id', nargs='?', default='all')
    parser.add_argument('--logging_level', default=30, type=int)
    args = parser.parse_args()

    setupLogging('log/augmentation/UploadCameraToES.log', args.logging_level, 'a')

    cam_db = Camera_ES_interface()

    if args.cam_id == 'all':
        logging.warning ('UploadCameraToES: doing for all')
        cam_id_paths = glob.glob(atcity('augmentation/scenes/cam*'))
        cam_ids = [op.basename(x)[3:] for x in cam_id_paths]
    else:
        cam_ids = [args.cam_id]
    print (cam_ids)

    for cam_id in cam_ids:
        if args.delete:
            print cam_db.delete_camera (cam_id)
        else:
            cam_path = atcity('augmentation/scenes/cam%s/cam%s.json' % (cam_id, cam_id))
            assert op.exists(cam_path), '%s' % cam_path
            cam_info = json.load(open(cam_path))
            print cam_db.update_camera (cam_info)
