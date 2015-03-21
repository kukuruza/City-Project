import logging
import sys
import os, os.path as op
import glob
sys.path.insert(0, os.path.abspath('../../learning'))
from utilities import setupLogging, get_CITY_DATA_PATH
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
        vec_name, ext = os.path.splitext(vec_name)
        part_path = op.join (op.dirname(vec_path), vec_name + '-' + part + ext)
        logging.info ('write ' + str(nlines) + ' lines to ' + part_path)

        with open(part_path, 'w') as f:
            for i in range(nlines):
                f.write (content[i])



def splitAllInDir (vec_dir, percentages):
    vec_template = op.join(vec_dir, '*.dat')
    vec_paths = glob.glob (vec_template)
    logging.info ('found ' + str(len(vec_paths)) + ' vector paths: ' + vec_template)
    for vec_path in vec_paths:
        splitVec (vec_path, percentages)


if __name__ == '__main__':

    CITY_DATA_PATH = get_CITY_DATA_PATH()
    setupLogging ('log/detector/splitVec.log', logging.INFO)

    vec_dir = op.join (CITY_DATA_PATH, 'learning/violajones/byname_24x18-2/car.dat')
    percentages = { 'train': 0.8, 'test': 0.2 }

    splitVec (vec_dir, percentages)

