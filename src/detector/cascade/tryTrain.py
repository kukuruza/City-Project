import logging
import sys
import os, os.path as op
sys.path.insert(0, os.path.abspath('../../learning'))
from utilities import setupLogging, get_CITY_DATA_PATH
from splitVec import splitVec
import random
from subprocess import call


def train (vec_path, params={}):

    dir_path='/Users/evg/projects/City-Project/data/learning/violajones/byname_24x18/';

    bg_in_path='../../../data/clustering/neg_bytype/negatives_for_car/*.jpg'
    bg_out_name='/Users/evg/projects/City-Project/data/learning/violajones/byname_24x18/bg.txt'

    #call(['ls', '-1', bg_in_path, '>', bg_out_name])
    #ls -1 ../../../clustering/neg_bytype/negatives_for_car/*.jpg > bg-car.txt

    name = dir_path + 'car-train'
    max_angle = '0.1'
    w = '24'
    h = '18'
    str_command = ['opencv_createsamples', '-vec', name + '.vec', '-bg', bg_out_name, 
                   '-info', name + '.dat', 
                   '-maxxangle', max_angle, '-maxyangle', max_angle, '-maxzangle', max_angle, 
                   '-num', '550', '-bgcolor', '128', '-w', w, '-h', h]
    ret = call(str_command);
    if ret != 0: 
        print ret
        sys.exit()

    model_name = dir_path + 'model-car-1'
    str_command = ['opencv_traincascade', '-data', model_name, '-vec', name + '.vec',
                '-bg', bg_out_name, '-numPos', '500', '-numNeg', '4000', '-w', w, '-h', h]
    print (' '.join(str_command))
    ret = call(str_command);


if __name__ == '__main__':

    CITY_DATA_PATH = get_CITY_DATA_PATH()
    setupLogging ('log/detector/violajones.log', logging.INFO, 'a')

    #vec_path = op.join (CITY_DATA_PATH, 'learning/violajones/cars_bysize/small.dat')
    #percentages = { 'train': 0.8, 'test': 0.2 }

    #splitVec (vec_path, percentages)

    train (op.join (CITY_DATA_PATH, 'learning/violajones/byname_24x18/car-train.dat'))
