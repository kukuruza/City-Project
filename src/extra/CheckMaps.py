import sys, os, os.path as op
import numpy as np
import cv2
from optparse import OptionParser


def checkMap (map_path, dtype='uint8', binary=False, channels=1, verbose=0):
    map_name = op.basename(map_path)
    if verbose:
        print (map_name)

    if not op.exists(map_path):
        print (map_name + ': file does not exist')
        return False

    # flag = -1 to load "as is"
    img = cv2.imread (map_path, -1)
    if img is None:
        print (map_name + ': problem withloading the image')
        return False

    # depth (8 bit vs 16 bit)
    if str(img.dtype) != dtype:
        print (map_name + ': dtype should be ' + dtype + ', but it is ' + str(img.dtype))
        return False

    # num of channels
    if len(list(img.shape)) == 2:
        if channels != 1:
            print (map_name + ': image have ' + str(channels) + ', but it grayscale')
            return False
    elif img.shape[2] != channels:
        print (map_name + ': image must have ' + str(channels) + 
               ' channel(s), but it has ' + str(img.shape[2]))
        return False

    # is it a binary image
    if binary and len(np.unique(img)) != 2:
        print (map_name + ': image must be binary ' +
               '(have pixels of exactly 2 distinct values), but ' +
               str(len(np.unique(img))) + ' values were found.')
        return False
    elif not binary and len(np.unique(img)) == 2:
        #cv2.imshow('test', img)
        #cv2.waitKey()
        print (map_name + ': image must NOT be binary ' +
               '(must have pixels of more than 2 distinct values)')
        return False

    return True



def checkSameSizes (paths):
    shape0 = None
    name0 = None

    for (path,status) in paths:
        # skip bad images
        if not status: continue
        # flag = 0 to load grayscale (shape is mantained)
        img = cv2.imread(path, 0)
        # init from the first image
        if shape0 is None: 
            shape0 = img.shape
            name0 = op.basename(path)
        # compare t0 shape0
        if img.shape != shape0:
            print ('shape between ' + op.basename(path) + ' differs from ' + name0)



def checkAcoversB (A_path, B_path):
    A_name = op.basename(A_path)
    B_name = op.basename(B_path)

    # flag = -1 to load "as is"
    imgA = cv2.imread(A_path, -1).astype('float')
    imgB = cv2.imread(B_path, -1).astype('float')
    if len(list(imgA.shape)) > 2: imgA = cv2.cvtColor(imgA, cv2.COLOR_BGR2GRAY)
    if len(list(imgB.shape)) > 2: imgB = cv2.cvtColor(imgB, cv2.COLOR_BGR2GRAY)

    #cv2.imshow('imgA', imgA)
    #cv2.waitKey()

    covered = np.count_nonzero (imgA[imgB != 0])
    total = np.count_nonzero (imgB != 0)
    ratio = 1 - float(covered) / total
    # thresolded because some values may happen to be zero
    Thresh = 0.01
    if ratio > Thresh:
        print (("%.1f" % (ratio * 100)) + '% elements of ' + op.basename(B_path) + 
               ' are not covered by ' + op.basename(A_path))



def checkMaps (map_path_template):
    size_map_path      = map_path_template.replace('*', 'Size')
    yaw_map_path       = map_path_template.replace('*', 'Yaw')
    pitch_map_path     = map_path_template.replace('*', 'Pitch')

    # check maps independently
    ok_size      = checkMap (size_map_path,      dtype='uint8')
    ok_yaw       = checkMap (yaw_map_path,       dtype='uint16')
    ok_pitch     = checkMap (pitch_map_path,     dtype='uint8')

    # sizes of all maps match
    checkSameSizes ([(size_map_path, ok_size),
                     (yaw_map_path, ok_yaw),
                     (pitch_map_path, ok_pitch)])

    # check that maps cover all that map_size has
    if ok_size and ok_yaw:
        checkAcoversB (yaw_map_path, size_map_path)
    if ok_size and ok_pitch:
        checkAcoversB (pitch_map_path, size_map_path)



if __name__ == '__main__':

    #setupHelper.setupLogging ('log/detector/runTrainTask.log', logging.INFO, 'a')

    parser = OptionParser(description='check geometry maps')
    parser.add_option('--map_path_template', type=str, help='maps/path/like/map-*.png')
    parser.add_option('-v', action='store_true', default=False, help='verbosity_level')
    (options, args) = parser.parse_args()

    checkMaps (options.map_path_template)

