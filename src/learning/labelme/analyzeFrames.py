import glob
import logging
import logging.handlers
import os
import os.path as OP
import sys
from analyzers import FrameAnalyzer
import carmodule
import cv2


def analyzeFolder (labelme_data_path, folder, backimage_path, geom_maps_dir):

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
        carmodule.saveMatCars (OP.join(car_dir, OP.basename(file_template + '.mat')), cars)



if __name__ == '__main__':
    ''' Demo '''

    __location__ = OP.realpath (OP.join(os.getcwd(), OP.dirname(__file__)))
    FORMAT = '%(asctime)s %(levelname)s: \t%(message)s'
    log_path = OP.join (__location__, 'logs.txt')
    logging.basicConfig (format=FORMAT, filename=log_path, level=logging.CRITICAL)

    labelme_data_path = '/Users/evg/projects/City-Project/data/labelme'
    folder = 'cam572-bright-frames'
    backimage_path = '/Users/evg/projects/City-Project/data/camdata/cam572/5pm/models/backimage.png'
    geom_maps_dir = '/Users/evg/projects/City-Project/data/models/cam572/'

    cars = analyzeFolder (labelme_data_path, folder, backimage_path=backimage_path,
        geom_maps_dir=geom_maps_dir)

    #cv2.imwrite ('testdata/test-patch.png', cars[0].patch)
    #cv2.imwrite ('testdata/test-ghost.png', cars[0].ghost)
    

