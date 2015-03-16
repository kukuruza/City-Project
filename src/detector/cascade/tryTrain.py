#!/bin/python

import logging
import sys
import os, os.path as op
sys.path.insert(0, os.path.abspath('../../learning'))
from utilities import setupLogging
from splitVec import splitVec
import random
from subprocess import call




def train (vec_path, params={}):

    bg_in_path = '../../../clustering/neg_bytype/negatives_for_car/*.jpg'
    bg_out_name = 'bg.txt'

    call(['ls', '-1', bg_in_path, '>', bg_out_name])
    #ls -1 ../../../clustering/neg_bytype/negatives_for_car/*.jpg > bg-car.txt

    name='car-train'
    max_angle = '0.1'
    w = '40'
    h = '30'
	ret = call(['opencv_createsamples', '-vec', name + '.vec', '-bg', bg_out_name, 
                '-info', name + '.dat', 
                '-maxxangle', max_angle, '-maxyangle', max_angle, '-maxzangle', max_angle, 
                '-num', '1000', '-bgcolor', '128', '-w', w, '-h', h]);
    if ret != 0: 
        print 
        sys.exit()

    model_name = 'model-car'
	ret = call(['opencv_traincascade', '-data', model_name, '-vec', name + '.vec',
                '-bg', bg_out_name, '-numPos', '1000', '-numNeg', '4000', '-w', w, '-h', h])






if __name__ == '__main__':

    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        raise Exception ('Set environmental variables CITY_PATH, CITY_DATA_PATH')
    CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')

    setupLogging ('log/detector/violajones.log', logging.INFO, 'a')

    #vec_path = op.join (CITY_DATA_PATH, 'learning/violajones/cars_bysize/small.dat')
    #percentages = { 'train': 0.8, 'test': 0.2 }

    #splitVec (vec_path, percentages)

    train (op.join (CITY_DATA_PATH, 'learning/violajones/byname_40x30-2/train-small.dat'))
