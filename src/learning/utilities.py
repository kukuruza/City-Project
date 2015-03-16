import numpy as np
import cv2
import sys, os, os.path as op
import logging, logging.handlers
import ConfigParser 


def setupLogging (filename, level=logging.INFO, filemode='w'):
    log = logging.getLogger('')
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s: \t%(message)s')
    log.setLevel(level)

    log_path = os.path.join (os.getenv('CITY_PATH'), filename)
    fh = logging.handlers.RotatingFileHandler(log_path, mode=filemode)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    log.addHandler(sh)


#
# roi - all inclusive, like in Matlab
# crop = im[roi[0]:roi[2]+1, roi[1]:roi[3]+1] (differs from Matlab)
#
def bbox2roi (bbox):
    assert (isinstance(bbox, list) and len(bbox) == 4)
    return [bbox[1], bbox[0], bbox[3]+bbox[1]-1, bbox[2]+bbox[0]-1]

def roi2bbox (roi):
    assert (isinstance(roi, list) and len(roi) == 4)
    return [roi[1], roi[0], roi[3]-roi[1]+1, roi[2]-roi[0]+1]

def image2ghost (image, backimage):
    assert (image is not None)
    assert (backimage is not None)
    return np.uint8((np.int32(image) - np.int32(backimage)) / 2 + 128)

def getCenter (roi):
    return (int((roi[0] + roi[2]) * 0.5), int((roi[1] + roi[3]) * 0.5))

def bottomCenter (roi):
    return (roi[0] * 0.25 + roi[2] * 0.75, roi[1] * 0.5 + roi[3] * 0.5)


def getCalibration ():
    CITY_PATH = os.environ.get('CITY_PATH')
    if not op.exists (op.join(CITY_PATH, 'etc')):
        os.mkdir (op.join(CITY_PATH, 'etc'))
    config_path = op.join(CITY_PATH, 'etc', 'config.ini')
    config = ConfigParser.ConfigParser()
    if op.exists (config_path):
        config.read(config_path)
        try:
           keys_dict = {}
           keys_dict['del']   = int(config.get('opencv_keys', 'del'))
           keys_dict['right'] = int(config.get('opencv_keys', 'right'))
           keys_dict['left']  = int(config.get('opencv_keys', 'left'))
           return keys_dict
        except:
           logging.info ('will calibrate the keys')
    cv2.imshow('dummy', np.zeros((10,10), dtype=np.uint8))
    config.add_section('opencv_keys')
    print ('please click on the opencv window and click "del"')
    keyd = cv2.waitKey(-1)
    config.set('opencv_keys', 'del', keyd)
    print ('please click on the opencv window and click "right arrow"')
    keyr = cv2.waitKey(-1)
    config.set('opencv_keys', 'right', keyr)
    print ('please click on the opencv window and click "left arrow"')
    keyl = cv2.waitKey(-1)
    config.set('opencv_keys', 'left', keyl)
    with open(config_path, 'a') as configfile:
        config.write(configfile)
    return { 'del': keyd, 'right': keyr, 'left': keyl }
