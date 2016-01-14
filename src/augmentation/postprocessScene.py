import sys, os, os.path as op
from glob import glob
from time import sleep, time
import json
import numpy as np
import cv2
from wand.image import Image, Color
from wand.display import display

sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/backend'))
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
import logging
import sqlite3
import datetime
import helperSetup
import helperDb
import helperImg
import utilities
from helperSetup import atcity
from video2dataset import video2dataset
from helperImg import ProcessorVideo
from helperSetup import _setupCopyDb_


RENDER_DIR = atcity('augmentation/render')
NORMAL_FILENAME   = 'normal.png'
CARSONLY_FILENAME = 'cars-only.png'
CAR_RENDER_TEMPL  = 'vehicle-'


def overlay_cars (background_path, carsonly_path, shadows_path, out_path):
    '''Put a png foreground on top of background and save as jpg
    '''
    assert op.exists (background_path)
    assert op.exists (carsonly_path)
    assert op.exists (shadows_path)

    with Image (filename=background_path) as back_img:
        img = Image(back_img)
        with Image (filename=carsonly_path) as cars_img:
            with Image (filename=shadows_path) as shadows_img:
                assert img.size == cars_img.size
                assert img.size == shadows_img.size
                sz = img.size

                # add unsharp mask
                cars_img.unsharp_mask (radius=20, sigma=3, amount=2, threshold=0.2)

                # overlay cars+shadows onto background
                img.composite_channel (channel='all_channels', 
                                       image=shadows_img, 
                                       operator='multiply', left=0, top=0)

                # put cars only onto background
                img.composite_channel (channel='all_channels', 
                                       image=cars_img, 
                                       operator='atop', left=0, top=0)

                img.save (filename=out_path)


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


def extract_annotations (c, frame_info, collection_info, render_dir, imagefile):
    '''Parse output of render and all metadata into our SQL format.
    This function knows about SQL format.
    Args:
        c:                cursor to existing db in our format
        frame_info:       info on the pose of every car in the frame, 
                          and its id within car collections
        collection_info:  info about car models
        render_dir:       TODO: put into frame_info
    Returns:
        nothing
    '''
    points = frame_info['vehicles']

    for i,point in enumerate(points):
        # get bbox
        render_png_path = op.join (render_dir, '%s%d.png' % (CAR_RENDER_TEMPL, i))
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



def postprocessFrame ():
    background_file = 'models/cam572/backimage-Nov28-10h.png'

    collection_dir = 'augmentation/CAD/7c7c2b02ad5108fe5f9082491d52810'
    traffic_file = 'augmentation/traffic/traffic-572.json'

    db_path    = op.join (RENDER_DIR, 'my_first_dummy.db')

    # load vehicle models data
    collection_path = atcity(op.join(collection_dir, '_collection_.json'))
    collection_info = json.load(open(collection_path))

    # create db-s
    conn = sqlite3.connect (db_path)
    helperDb.createDb(conn)
    c = conn.cursor()

    traffic_path = atcity(traffic_file)
    frame_info = json.load(open( traffic_path ))

    image_path = op.join (RENDER_DIR, 'out.jpg')
    mask_path  = op.join (RENDER_DIR, 'mask.jpg')

    # put cars render on top of background
    overlay_cars (atcity(background_file), 
                  op.join(RENDER_DIR, CARSONLY_FILENAME), 
                  op.join(RENDER_DIR, NORMAL_FILENAME), 
                  image_path)

    # create mask
    imagefile = image_path
    maskfile = mask_path
    carsonly = cv2.imread( op.join(RENDER_DIR, CARSONLY_FILENAME), -1 )
    assert carsonly.shape[2] == 4   # need the alpha channel
    mask = np.array(carsonly[:,:,3] > 0).astype(np.uint8) * 255
    cv2.imwrite (mask_path, mask)

    height = mask.shape[0]
    width  = mask.shape[1]
    src = 'TBD'
    timestamp = 'TBD'
    image_entry = (imagefile,maskfile,src,width,height,timestamp)
    s = 'images(imagefile,maskfile,src,width,height,time)'
    c.execute ('INSERT INTO %s VALUES (?,?,?,?,?,?)' % s, image_entry)

    extract_annotations (c, frame_info, collection_info, RENDER_DIR, imagefile)

    conn.commit()
    conn.close()



def postprocessVideo ():
    collection_dir = 'augmentation/CAD/7c7c2b02ad5108fe5f9082491d52810'
    traffic_file = 'augmentation/traffic/traffic.json'
    db_file_in = 'databases/augmentation/Nov28-10h-back.db'

    video_out_dir = 'augmentation/video'
    db_file_out = 'databases/augmentation/Nov28-10h-traffic.db'

    helperSetup.setupLogging ('log/augmentation/postprocessScene.log', logging.INFO, 'a')

    # load vehicle models data
    collection_path = atcity(op.join(collection_dir, '_collection_.json'))
    collection_info = json.load(open(collection_path))

    # copy input db to output and open it
    _setupCopyDb_ (atcity(db_file_in), atcity(db_file_out))
    conn = sqlite3.connect (atcity(db_file_out))
    c = conn.cursor()

    name = op.basename(op.splitext(db_file_out)[0])
    logging.info ('new src name: %s' %  name)

    # names of in and out videos
    c.execute('SELECT imagefile,maskfile FROM images')
    some_image_entry = c.fetchone()
    in_back_video_file  = op.dirname(some_image_entry[0]) + '.avi'
    in_mask_video_file  = op.dirname(some_image_entry[1]) + '.avi'
    out_image_video_file = op.join(video_out_dir, name + '.avi')
    out_mask_video_file  = op.join(video_out_dir, name + '-mask.avi')
    logging.info ('postprocessVideo: in back_video_file:   %s' % in_back_video_file)
    logging.info ('postprocessVideo: in mask_video_file:   %s' % in_mask_video_file)
    logging.info ('postprocessVideo: out image_video_file: %s' % out_image_video_file)
    logging.info ('postprocessVideo: out mask_video_file:  %s' % out_mask_video_file)

    processor = ProcessorVideo \
           ({'out_dataset': {in_back_video_file: out_image_video_file, 
                             in_mask_video_file: out_mask_video_file} })

    # which frames from back_video_file we will use:
    #   right now, sequentially, starting from frame_start
    #frame_start = 50
    #for i in range(frame_start):
    #    ret = back_video.read()
    #    assert ret is not None, 'background video stopped at frame %d' % i

    video_info = json.load(open( atcity(traffic_file) ))
 
    c.execute('SELECT imagefile,maskfile FROM images')
    for (in_backfile, in_maskfile) in c.fetchall():
        i_str = op.splitext(op.basename(in_backfile))[0]
        render_dir = op.join(RENDER_DIR, 'fr-%s' % i_str)
        logging.info ('process frame %s' % i_str)

        # check if rendered frame exists
        if not op.exists (op.join(render_dir)):
            logging.warning('do not have rendered frames for imagefile #%s' % i_str)
            continue

        # background image from the video
        back = processor.imread(in_backfile)
        in_mask = processor.imread(in_maskfile)

        # put cars render on top of background
        # communication via temporary files because Wand and NumPy do not talk to each other
        background_path = '/tmp/postProcessframe-back.png'
        image_path      = '/tmp/postProcessframe-image.png'
        cv2.imwrite (background_path, back)
        overlay_cars (background_path, 
                      op.join(render_dir, CARSONLY_FILENAME), 
                      op.join(render_dir, NORMAL_FILENAME), 
                      image_path)
        image = cv2.imread(image_path)

        # create mask
        carsonly = cv2.imread( op.join(render_dir, CARSONLY_FILENAME), -1 )
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

        frame_info = video_info[int(i_str)]
        extract_annotations (c, frame_info, collection_info, render_dir, out_imagefile)

    conn.commit()
    conn.close()

    



# test this script
if __name__ == "__main__":
    postprocessVideo ()