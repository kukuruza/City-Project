#!/bin/python

import logging
import sys
import os, os.path as op
sys.path.insert(0, os.path.abspath('../../learning'))
from utilities import setupLogging
import random


def splitVec (vec_path, percentages):

    with open(vec_path) as f:
        content = f.readlines()

    logging.info ('there are ' + str(len(content)) + ' lines in ' + vec_path)

    random.seed(0)
    random.shuffle(content)

    for (part,perc) in percentages.iteritems():

        nlines = int(len(content) * perc)

        vec_name = op.basename(vec_path)
        part_path = op.join (op.dirname(vec_path), part + '-' + vec_name)
        logging.info ('write ' + str(nlines) + ' lines to ' + part_path)

        with open(part_path, 'w') as f:
            for i in range(nlines):
                f.write (content[i] + '\n')



if __name__ == '__main__':

    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        raise Exception ('Set environmental variables CITY_PATH, CITY_DATA_PATH')
    CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')

    setupLogging ('log/detector/splitVec.log', logging.INFO)

    vec_path = op.join (CITY_DATA_PATH, 'learning/violajones/cars_bysize/small.dat')
    percentages = { 'train': 0.8, 'test': 0.2 }

    splitVec (vec_path, percentages)

