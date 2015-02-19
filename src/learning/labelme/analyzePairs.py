# Parse labelme vstacked images into car-matches between frames
#
# Script takes a 'folder' name. 
# /Images/folder and /Annotations/folder are the results of the labelme,
#   Each image is two vertically stacked frames
#   Labelme annotations signify matches between frames
#
# The output is a number of files with names like f000-001-N.mat, 
#   which keeps the match of car N between frames 0 and 1 as {car1, car2}
#

import glob
import logging
import logging.handlers
import os, sys
import os.path as OP
import shutil
import cv2
from analyzers import PairAnalyzer

if not os.environ.get('CITY_PATH'):
    print 'First set the environmental variable CITY_PATH'
    sys.exit()
else:
    sys.path.insert(0, OP.join(os.getenv('CITY_PATH'), 'src'))
from pycar.pycar import Car, saveMatCars


def analyzeFolder (folder, labelme_data_path, backimage_path, geom_maps_dir):

    analyzer = PairAnalyzer()
    analyzer.setPaths (labelme_data_path, backimage_path, geom_maps_dir)

    pathlist = glob.glob (OP.join(labelme_data_path, 'Annotations', folder, '*.xml'))

    # delete the folder in 'Car' dir, and recreate it
    car_dir = OP.join (labelme_data_path, 'PyCars', folder)
    shutil.rmtree (car_dir)
    os.makedirs (car_dir)


    for path in pathlist:
        logging.debug ('processing file ' + OP.basename(path))
        car_pairs = analyzer.processImage(folder, OP.basename(path))

        file_template, extention = OP.splitext(path)
        for i in range(len(car_pairs)):
            car_pair_name = OP.basename (file_template + '-' + str(i) + '.mat')
            car_pair_path = OP.join (car_dir, car_pair_name)
            car1, car2 = car_pairs[i]
            saveMatCars (car_pair_path, [car1, car2])



if __name__ == '__main__':
    ''' Demo '''

    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        print 'First set the environmental variable CITY_PATH, CITY_DATA_PATH'
        sys.exit()
    else:
        CITY_PATH = os.getenv('CITY_PATH')
        CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')

    FORMAT = '%(asctime)s %(levelname)s: \t%(message)s'
    log_path = OP.join (CITY_PATH, 'log/learning/labelme/analyzePairs.log')
    logging.basicConfig (format=FORMAT, filename=log_path, level=logging.INFO)

    folder = 'cam572-5pm-pairs'
    labelme_data_path = OP.join (CITY_DATA_PATH, 'labelme')
    backimage_path = OP.join (CITY_DATA_PATH, 'camdata/cam572/5pm/models/backimage.png')
    geom_maps_dir = OP.join (CITY_DATA_PATH, 'models/cam572/')

    cars = analyzeFolder (folder, 
                          labelme_data_path=labelme_data_path,
                          backimage_path=backimage_path,
                          geom_maps_dir=geom_maps_dir)
    

