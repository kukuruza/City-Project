import sys, os, os.path as op
from glob import glob
from time import sleep, time
import json
import numpy as np
import cv2
import argparse

sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/backend'))
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
import logging
import sqlite3
import datetime
import helperSetup
import helperDb
import helperImg
import utilities
import subprocess
import shutil
from video2dataset import video2dataset
from helperImg import ProcessorVideo
from helperSetup import _setupCopyDb_, setupLogging
from placeCars import generate_current_frame

# All rendering by blender takes place in WORK_DIR
WORK_DIR          = op.join(os.getenv('CITY_DATA_PATH'), 'augmentation/render/current-frame')
TRAFFIC_WORK_PATH = op.join(os.getenv('CITY_DATA_PATH'), 'augmentation/traffic/current-frame.json')
BACKGROUND_FILENAME = 'background.png'
NORMAL_FILENAME     = 'normal.png'
CARSONLY_FILENAME   = 'cars-only.png'
COMBINED_FILENAME   = 'out.png'
MASK_FILENAME       = 'mask.png'

blender_path = '/Applications/blender.app/Contents/MacOS/blender'



def image2ghost (image_path, background_path, out_path):
    '''Subtract background from image and save as the ghost frame
    '''
    img  = cv2.imread(image_path)
    back = cv2.imread(background_path)
    ghost = img / 2 + 128 - back / 2
    np.imwrite(ghost, out_path)


def extract_bbox (render_png_path):
    '''Extract a single (if any) bounding box from the image
    Args:
      render_png_path:  has only one (or no) car in the image.
    Returns:
      bbox:  (x1, y1, width, height)
    '''
    if not op.exists(render_png_path):
        logging.error ('Car render image does not exist: %s' % render_png_path)
    vehicle_render = cv2.imread(render_png_path, -1)
    assert vehicle_render.shape[2] == 4   # need alpha channel
    alpha = vehicle_render[:,:,3]
    
    # keep only vehicles with resonable bboxes
    if np.count_nonzero(alpha) == 0:   # or are there any artifacts
        return None

    # get bbox
    nnz_indices = np.argwhere(alpha)
    (y1, x1), (y2, x2) = nnz_indices.min(0), nnz_indices.max(0) + 1 
    (height, width) = y2 - y1, x2 - x1
    return (x1, y1, width, height)


def _find_carmodel_by_id_ (collection_info, model_id):
    # TODO: replace sequential search with an elasticsearch index
    for carmodel in collection_info['vehicles']:
        if carmodel['model_id'] == model_id:
            return carmodel
    return None


def extract_annotations (c, frame_info, collection_info, imagefile):
    '''Parse output of render and all metadata into our SQL format.
    This function knows about SQL format.
    Args:
        c:                cursor to existing db in our format
        frame_info:       info on the pose of every car in the frame, 
                          and its id within car collections
        collection_info:  info about car models
        imagefile:        database entry
    Returns:
        nothing
    '''
    points = frame_info['vehicles']

    for i,point in enumerate(points):
        # get bbox
        render_png_path = op.join (WORK_DIR, 'vehicle-%d.png' % i)
        bbox = extract_bbox (render_png_path)
        if bbox is None: continue

        # get vehicle "name" (that is, type)
        carmodel = _find_carmodel_by_id_ (collection_info, point['model_id'])
        assert carmodel is not None
        name = carmodel['vehicle_type']

        # put all info together and insert into the db
        entry = (imagefile, name, bbox[0], bbox[1], bbox[2], bbox[3], None)
        c.execute('''INSERT INTO cars(imagefile,name,x1,y1,width,height,score) 
                     VALUES (?,?,?,?,?,?,?);''', entry)



def process_current_frame (args):
    ''' Full stack for one single frame (no db entries). All work is in current-frame dir.
    '''
    # get input for this job from json
    job_info = json.load(open(args.job_path))
    render_scene_path    = op.join(args.rel_path, job_info['render_scene_file'])
    combine_scene_path   = op.join(args.rel_path, job_info['combine_scene_file'])

    if not args.no_traffic:
        # generate traffic
        timestamp = datetime.datetime.strptime(args.start_time, '%Y-%m-%d %H:%M:%S.%f')
        generate_current_frame(timestamp)

    if not args.no_render:
        # remove so that they do not exist if blender fails
        if op.exists(op.join(WORK_DIR, NORMAL_FILENAME)):
            os.remove(op.join(WORK_DIR, NORMAL_FILENAME))
        if op.exists(op.join(WORK_DIR, CARSONLY_FILENAME)):
            os.remove(op.join(WORK_DIR, CARSONLY_FILENAME))
        # render
        command = '%s %s --background --python %s/src/augmentation/renderScene.py' % \
                  (blender_path, render_scene_path, os.getenv('CITY_PATH'))
        returncode = subprocess.call ([command], shell=True)
        logging.info ('rendering: blender returned code %s' % str(returncode))

    if not args.no_combine:
        # remove so that they do not exist if blender fails
        if op.exists(op.join(WORK_DIR, COMBINED_FILENAME)): 
            os.remove(op.join(WORK_DIR, COMBINED_FILENAME))
        # postprocess and overlay
        command = '%s %s --background --python %s/src/augmentation/combineFrame.py' % \
                  (blender_path, combine_scene_path, os.getenv('CITY_PATH'))
        returncode = subprocess.call ([command], shell=True)
        logging.info ('combine: blender returned code %s' % str(returncode))
        assert op.exists(op.join(WORK_DIR, COMBINED_FILENAME))

        # create mask
        mask_path  = op.join(WORK_DIR, MASK_FILENAME)
        carsonly = cv2.imread( op.join(WORK_DIR, CARSONLY_FILENAME), -1 )
        assert carsonly.shape[2] == 4   # need the alpha channel
        mask = np.array(carsonly[:,:,3] > 0).astype(np.uint8) * 255
        cv2.imwrite (mask_path, mask)



def process_video (args):

    # get input for this job from json
    job_info = json.load(open(args.job_path))
    in_db_path           = op.join(args.rel_path, job_info['in_db_file'])
    out_db_path          = op.join(args.rel_path, job_info['out_db_file'])
    out_image_video_file = job_info['out_image_video_file']
    out_mask_video_file  = job_info['out_mask_video_file']
    out_image_video_path = op.join(args.rel_path, job_info['out_image_video_file'])
    out_mask_video_path  = op.join(args.rel_path, job_info['out_mask_video_file'])
    render_scene_path    = op.join(args.rel_path, job_info['render_scene_file'])
    combine_scene_path   = op.join(args.rel_path, job_info['combine_scene_file'])

    # load vehicle models data
    collection_dir = 'augmentation/CAD/7c7c2b02ad5108fe5f9082491d52810'
    collection_path = op.join(os.getenv('CITY_DATA_PATH'), collection_dir, '_collection_.json')
    collection_info = json.load(open(collection_path))

    # copy input db to output and open it
    _setupCopyDb_ (in_db_path, out_db_path)
    conn = sqlite3.connect (out_db_path)
    c = conn.cursor()

    # remove video if exist
    if op.exists(out_image_video_path): os.remove(out_image_video_path)
    if op.exists(out_mask_video_path):  os.remove(out_mask_video_path)

    name = op.basename(op.splitext(out_db_path)[0])
    logging.info ('new src name: %s' %  name)

    # names of in and out videos
    c.execute('SELECT imagefile,maskfile FROM images')
    some_image_entry = c.fetchone()
    in_back_video_file  = op.dirname(some_image_entry[0]) + '.avi'
    in_mask_video_file  = op.dirname(some_image_entry[1]) + '.avi'
    logging.info ('in back_video_file:   %s' % in_back_video_file)
    logging.info ('in mask_video_file:   %s' % in_mask_video_file)
    logging.info ('out image_video_file: %s' % out_image_video_file)
    logging.info ('out mask_video_file:  %s' % out_mask_video_file)

    processor = ProcessorVideo \
           ({'rel_path': args.rel_path,
             'out_dataset': {in_back_video_file: out_image_video_file, 
                             in_mask_video_file: out_mask_video_file} })

    start_time = datetime.datetime.strptime('2015-01-13 09:30', '%Y-%m-%d %H:%M')

    c.execute('SELECT imagefile,maskfile FROM images')
    for (in_backfile, in_maskfile) in c.fetchall():
        i_str = op.splitext(op.basename(in_backfile))[0]
        logging.info ('process frame %s' % i_str)

        # background image from the video
        back = processor.imread(in_backfile)
        in_mask = processor.imread(in_maskfile)

        # check that the background is already there (if static_back) or write it down there
        if not args.static_back:
            cv2.imwrite (op.join(WORK_DIR, BACKGROUND_FILENAME), back)
        assert op.exists(op.join(WORK_DIR, BACKGROUND_FILENAME))

        if not args.no_traffic:
            # generate traffic
            timestamp = datetime.datetime.strptime(args.start_time, '%Y-%m-%d %H:%M:%S.%f')
            generate_current_frame(timestamp + datetime.timedelta(minutes=int(float(i_str) / 960 * 40)))

        if not args.no_render:
            # remove so that they do not exist if blender fails
            if op.exists(op.join(WORK_DIR, NORMAL_FILENAME)):
                os.remove(op.join(WORK_DIR, NORMAL_FILENAME))
            if op.exists(op.join(WORK_DIR, CARSONLY_FILENAME)):
                os.remove(op.join(WORK_DIR, CARSONLY_FILENAME))
            # render
            command = '%s %s --background --python %s/src/augmentation/renderScene.py' % \
                      (blender_path, render_scene_path, os.getenv('CITY_PATH'))
            returncode = subprocess.call ([command], shell=True)
            logging.info ('rendering: blender returned code %s' % str(returncode))

        if not args.no_combine:
            # remove so that they do not exist if blender fails
            if op.exists(op.join(WORK_DIR, COMBINED_FILENAME)): 
                os.remove(op.join(WORK_DIR, COMBINED_FILENAME))
            # postprocess and overlay
            command = '%s %s --background --python %s/src/augmentation/combineFrame.py' % \
                      (blender_path, combine_scene_path, os.getenv('CITY_PATH'))
            returncode = subprocess.call ([command], shell=True)
            logging.info ('combine: blender returned code %s' % str(returncode))
            image = cv2.imread(op.join(WORK_DIR, COMBINED_FILENAME))

            # create mask
            mask_path  = op.join(WORK_DIR, MASK_FILENAME)
            carsonly = cv2.imread( op.join(WORK_DIR, CARSONLY_FILENAME), -1 )
            assert carsonly.shape[2] == 4   # need the alpha channel
            mask = carsonly[:,:,3] > 0

        # write the frame to video (processor interface requires input filenames)
        processor.imwrite (image, in_backfile)
        processor.maskwrite (mask, in_maskfile)

        # update the filename in database
        out_imagefile = op.join(op.splitext(out_image_video_file)[0], op.basename(in_backfile))
        out_maskfile  = op.join(op.splitext(out_mask_video_file)[0], op.basename(in_maskfile))
        c.execute('UPDATE images SET imagefile=?, maskfile=? WHERE imagefile=?', 
                    (out_imagefile, out_maskfile, in_backfile))

        frame_info = json.load(open( TRAFFIC_WORK_PATH ))
        extract_annotations (c, frame_info, collection_info, out_imagefile)

        if args.num_frames > 0 and int(i_str) >= args.num_frames: 
            break

    conn.commit()
    conn.close()

    



# test this script
if __name__ == "__main__":

    setupLogging('log/augmentation/processScene.log', logging.INFO, 'a')

    parser = argparse.ArgumentParser()
    parser.add_argument('--no_traffic', action='store_true')
    parser.add_argument('--no_render',  action='store_true')
    parser.add_argument('--no_combine', action='store_true')
    parser.add_argument('--static_back', action='store_true')
    parser.add_argument('--start_time', nargs='?', default='2014-01-13 10:15:14.001') # temporary
    parser.add_argument('--num_frames', nargs='?', default=-1, type=int)
    parser.add_argument('--rel_path', nargs='?', default=os.getenv('CITY_DATA_PATH'))
    parser.add_argument('--job_path')
    args = parser.parse_args()

    # process_current_frame(args)
    process_video(args)

