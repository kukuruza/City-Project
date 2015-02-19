import glob
import logging
import logging.handlers
import os
import os.path as OP
import shutil
from analyzers import FrameAnalyzer
import cv2

import sys
if not os.environ.get('CITY_PATH'):
    print 'First set the environmental variable CITY_PATH'
    sys.exit()
else:
    sys.path.insert(0, OP.join(os.getenv('CITY_PATH'), 'src'))
from pycar.pycar import Car, saveMatCars


def analyzeFolder (folder, labelme_data_path, backimage_path, geom_maps_dir):

    analyzer = FrameAnalyzer()
    analyzer.setPaths (labelme_data_path, backimage_path, geom_maps_dir)

    pathlist = glob.glob (OP.join(labelme_data_path, 'Annotations', folder, '*.xml'))

    # delete the folder in 'Car' dir, and recreate it
    car_dir = OP.join (labelme_data_path, 'PyCars', folder)
    shutil.rmtree (car_dir)
    os.makedirs (car_dir)

    for path in pathlist:
        logging.debug ('processing file ' + OP.basename(path))
        cars = analyzer.processImage(folder, OP.basename(path))

        file_template, extention = OP.splitext(path)
        saveMatCars (OP.join(car_dir, OP.basename(file_template + '.mat')), cars)



if __name__ == '__main__':
    ''' Demo '''

    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        print 'First set the environmental variable CITY_PATH, CITY_DATA_PATH'
        sys.exit()
    else:
        CITY_PATH = os.getenv('CITY_PATH')
        CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')

    FORMAT = '%(asctime)s %(levelname)s: \t%(message)s'
    log_path = OP.join (CITY_PATH, 'log/learning/labelme/analyzeFrames.log')
    logging.basicConfig (format=FORMAT, filename=log_path, level=logging.INFO)

    folder = 'cam572-bright-frames'
    labelme_data_path = OP.join (CITY_DATA_PATH, 'labelme')
    backimage_path = OP.join (CITY_DATA_PATH, 'camdata/cam572/5pm/models/backimage.png')
    geom_maps_dir = OP.join (CITY_DATA_PATH, 'models/cam572/')

    cars = analyzeFolder (folder,
                          labelme_data_path=labelme_data_path, 
                          backimage_path=backimage_path,
                          geom_maps_dir=geom_maps_dir)

    #cv2.imwrite ('testdata/test-patch.png', cars[0].patch)
    #cv2.imwrite ('testdata/test-ghost.png', cars[0].ghost)
    

