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
    points = frame_info['poses']

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


# test this script
if __name__ == "__main__":

    background_file = 'models/cam572/backimage-Nov28-10h.png'

    collection_dir = '/Users/evg/Downloads/7c7c2b02ad5108fe5f9082491d52810'

    render_dir = atcity('augmentation/render')

    image_path = op.join (render_dir, 'out.jpg')
    mask_path  = op.join (render_dir, 'mask.jpg')
    db_path    = op.join (render_dir, 'my_first_dummy.db')

    collection_dir = 'augmentation/CAD/7c7c2b02ad5108fe5f9082491d52810'
    traffic_file = 'augmentation/traffic/traffic-572.json'

    # put cars render on top of background
    overlay_cars (atcity(background_file), 
                  op.join(render_dir, CARSONLY_FILENAME), 
                  op.join(render_dir, NORMAL_FILENAME), 
                  image_path)

    # create mask
    imagefile = image_path
    maskfile = mask_path
    carsonly = cv2.imread( op.join(render_dir, CARSONLY_FILENAME), -1 )
    assert carsonly.shape[2] == 4   # need the alpha channel
    mask = np.array(carsonly[:,:,3] > 0).astype(np.uint8) * 255
    cv2.imwrite (mask_path, mask)

    # load vehicle models data
    collection_path = atcity(op.join(collection_dir, '_collection_.json'))
    collection_info = json.load(open(collection_path))

    # create db-s
    conn = sqlite3.connect (db_path)
    helperDb.createDb(conn)
    c = conn.cursor()

    height = mask.shape[0]
    width  = mask.shape[1]
    src = 'TBD'
    timestamp = 'TBD'
    image_entry = (imagefile,maskfile,src,width,height,timestamp)
    s = 'images(imagefile,maskfile,src,width,height,time)'
    c.execute ('INSERT INTO %s VALUES (?,?,?,?,?,?)' % s, image_entry)

    traffic_path = atcity(traffic_file)
    traffic_info = json.load(open( traffic_path ))

    extract_annotations (c, traffic_info, collection_info, render_dir, imagefile)

    conn.commit()
    conn.close()
