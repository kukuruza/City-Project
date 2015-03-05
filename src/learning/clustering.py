#!/usr/bin/python
#
# Clustering aims to prepare Car/PyCar objects collected from different sources
#   into dataset that can be used for training/testing.
#
# The input of the module is collections of cars, the output is folders 
#   with patches that meet specified requirements (e.g. orientation.)
#
# Clustering cars based by orientation/size/type/color is set by user.
# The sources of objects are set in a config files.
# Format of output dataset can be different for different packages.
# Maybe splitting into training/testing can be done here.
#

IMAGE_EXT = '.png'


import logging
import os, sys
import os.path as OP
import shutil
import glob
import json
import numpy as np, cv2
from dbInterface import queryCars, queryField



def image2ghost (image, backimage):
    assert (image is not None)
    assert (backimage is not None)
    return np.uint8((np.int32(image) - np.int32(backimage)) / 2 + 128)



def getGhost (labelme_dir, car_entry, backimage):
    assert (car_entry is not None)
    #print (car_entry)

    carid = queryField (car_entry, 'id')
    imagefile = queryField (car_entry, 'imagefile')
    width = queryField (car_entry, 'width')
    height = queryField (car_entry, 'height')
    offsetx = queryField (car_entry, 'offsetx')
    offsety = queryField (car_entry, 'offsety')
    x1 = offsetx + queryField (car_entry, 'x1')
    y1 = offsety + queryField (car_entry, 'y1')

    imagepath = OP.join (labelme_dir, 'Images', imagefile)
    if not OP.exists (imagepath):
        raise Exception ('imagepath does not exist: ' + imagepath)
    image = cv2.imread(imagepath)
    ghostimage = image2ghost (image, backimage)

    ghost = ghostimage [y1:y1+height, x1:x1+width]
    return (carid, imagefile, ghost)



def collectGhosts (db_path, filters_path, labelme_dir, backimage_path, out_dir):
    '''Cluster cars and save the patches by cluster

       Find cars in paths specified in data_list_path,
       use filters to cluster and transform,
       and save the ghosts '''

    # load backimage
    if not OP.exists (backimage_path):
        raise Exception ('no backimage at path ' + backimage_path)
    backimage = cv2.imread(backimage_path)

    # load clusters
    if not OP.exists(filters_path):
        raise Exception('filters_path does not exist: ' + filters_path)
    filters_file = open(filters_path)
    filters_groups = json.load(filters_file)
    filters_file.close()

    counter_by_cluster = {}

    for filter_group in filters_groups:
        assert ('filter' in filter_group)
        cluster_dir = OP.join (out_dir, filter_group['filter'])

        # delete 'cluster_dir' dir, and recreate it
        if OP.exists (cluster_dir):
            shutil.rmtree (cluster_dir)
        os.makedirs (cluster_dir)

        # get db entries
        car_entries = queryCars (db_path, filter_group)
        counter_by_cluster[filter_group['filter']] = len(car_entries)

        # write ghosts for each entry
        for car_entry in car_entries:
            carid, filename, ghost = getGhost (labelme_dir, car_entry, backimage)

            filename = "%08d" % carid + IMAGE_EXT
            filepath = OP.join(cluster_dir, filename)

            if 'resize' in filter_group.keys():
                assert (type(filter_group['resize']) == list)
                assert (len(filter_group['resize']) == 2)
                ghost = cv2.resize(ghost, tuple(filter_group['resize']))

            cv2.imwrite(filepath, ghost)

    return counter_by_cluster




#
# Collect negative patches around car patches
#
def collectNegatives (db_path, filters_path, labelme_dir, backimage_path, 
                      out_dir, options={}):

    # options
    #mult_samples = options['mult_samples'] if 'mult_samples' in options.keys else 5

    # load backimage
    if not OP.exists (backimage_path):
        raise Exception ('no backimage at path ' + backimage_path)
    backimage = cv2.imread(backimage_path)

    # load clusters
    if not OP.exists(filters_path):
        raise Exception('filters_path does not exist: ' + filters_path)
    filters_file = open(filters_path)
    filters_groups = json.load(filters_file)
    filters_file.close()

    counter_by_cluster = {}

    for filter_group in filters_groups:
        assert ('filter' in filter_group)
        cluster_dir = OP.join (out_dir, filter_group['filter'])

        # delete 'cluster_dir' dir, and recreate it
        if OP.exists (cluster_dir):
            shutil.rmtree (cluster_dir)
        os.makedirs (cluster_dir)

        # get names of image file
        imagefiles = queryCars (db_path, filter_group, ['DISTINCT imagefile'])
        logging.debug ('got ' + str(len(imagefiles)) + ' imagefiles')

        for imagefile in imagefiles:
            imagefile = imagefile[0]

            # get cars inside this file
            filter_group_file = filter_group
            filter_group['imagefile'] = imagefile
            car_entries = queryCars (db_path, filter_group)
            logging.info ('for imagefile ' + OP.basename(imagefile) + 
                           ' got ' + str(len(car_entries)) + ' cars')

            # load the image and get the ghost
            image = cv2.imread(OP.join(labelme_dir, 'Images', imagefile))
            (height, width, depth) = image.shape
            ghost = image2ghost (image, backimage)

            # put a circle inside every car
            for car in car_entries:
                print (car)
                x1 = queryField(car,'x1')
                y1 = queryField(car,'y1')
                halfh = queryField(car,'height') / 2
                halfw = queryField(car,'width') / 2
                center = (y1 + halfh, x1 + halfw)
                #cv2.ellipse (ghost, center, (halfh,halfw), 0,0,360,(255,0,0),-1)
                cv2.rectangle (ghost, (x1, y1), (x1+halfw*2, y1+halfh*2), (255,0,0))

            cv2.imshow ('test', ghost)
            cv2.waitKey(-1)







