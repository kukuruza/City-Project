import sys, os, os.path as op
import argparse
import subprocess
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
from helperSetup import setupLogging, atcity


def upload_mask_back(args):

    with open(atcity(args.list_file)) as f:
        lines = f.readlines()
        lines = [line for line in lines if line and line[0] != '#']
        cam_names = [line.split()[0] for line in lines]

    for cam_name in cam_names:
        video_dir = op.join('camdata', 'cam%s' % cam_name, args.video_dir_name)
        mask_path  = atcity(op.join(video_dir, 'mask.avi'))
        back_path  = atcity(op.join(video_dir, 'back.avi'))
        ghost_path = atcity(op.join(video_dir, 'ghost.avi'))
        paths = [mask_path, back_path, ghost_path]
        for path in paths:
            server_dir = op.join('etoropov@mouragroup.org:~/projects/City-Project/data/', video_dir) 
            command = 'scp %s %s' % (path, server_dir)
            print command
            returncode = subprocess.call ([command], shell=True)
            print 'scp finished with code %s' % returncode


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--upload_mask_back', action='store_true', help='if enabled, will upload')
    parser.add_argument('--list_file')
    parser.add_argument('--video_dir_name')
    args = parser.parse_args()

    upload_mask_back(args)