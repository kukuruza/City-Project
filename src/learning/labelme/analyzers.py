import numpy as np
import cv2
import xml.etree.ElementTree as ET
import os, sys
import collections
import logging
import os.path as OP

sys.path.insert(0, os.path.abspath('annotations'))
from annotations.parser import FrameParser, PairParser

if not os.environ.get('CITY_PATH'):
    print 'First set the environmental variable CITY_PATH'
    sys.exit()
else:
    sys.path.insert(0, OP.join(os.getenv('CITY_PATH'), 'src'))
from pycar.pycar import Car



#
# roi - all inclusive, like in Matlab
# crop = im[roi[0]:roi[2]+1, roi[1]:roi[3]+1] (differs from Matlab)
#


def roi2bbox (roi):
    assert (isinstance(roi, list) and len(roi) == 4)
    return [roi[1], roi[0], roi[3]-roi[1]+1, roi[2]-roi[0]+1]

def image2ghost (image, backimage):
    return np.uint8((np.int32(image) - np.int32(backimage)) / 2 + 128)


class BaseAnalyzer:

    border_thresh_perc = 0.03
    expand_perc = 0.1
    ratio = 0.75

    def setPaths (self, labelme_data_path, backimage_path, geom_maps_dir):        
        if not OP.exists (backimage_path):
            raise Exception ('no backimage at path ' + backimage_path)
        self.backimage = cv2.imread(backimage_path)
        self.loadMaps(geom_maps_dir)

        self.labelme_data_path = labelme_data_path


    # this function knows all about size- and orientation- maps
    def loadMaps (self, geom_maps_dir):
        size_map_path  = OP.join (geom_maps_dir, 'sizeMap.tiff')
        pitch_map_path = OP.join (geom_maps_dir, 'pitchMap.tiff')
        yaw_map_path   = OP.join (geom_maps_dir, 'yawMap.tiff')
        self.size_map  = cv2.imread (size_map_path, 0).astype(np.float32)
        self.pitch_map = cv2.imread (pitch_map_path, 0).astype(np.float32)
        self.yaw_map   = cv2.imread (yaw_map_path, -1).astype(np.float32)
        self.yaw_map   = cv2.add (self.yaw_map, -360)

    
    def imageOfAnnotation (self, annotation):
        folder = annotation.find('folder').text
        imagename = annotation.find('filename').text
        imagepath = OP.join (self.labelme_data_path, 'Images', folder, imagename)
        if not OP.exists (imagepath):
            raise Exception ('no image at path ' + imagepath)
        return cv2.imread(imagepath)


    def pointsOfPolygon (self, annotation):
        pts = annotation.find('polygon').findall('pt')
        xs = []
        ys = []
        for pt in pts:
            xs.append( int(pt.find('x').text) )
            ys.append( int(pt.find('y').text) )
        return xs, ys


    def isDegeneratePolygon (self, xs, ys):
        return len(xs) <= 2 or min(xs) == max(xs) or min(ys) == max(ys)


    def isPolygonAtBorder (self, xs, ys, width, height):
        border_thresh = (height + width) / 2 * self.border_thresh_perc
        dist_to_border = min (xs, [width - x for x in xs], ys, [height - y for y in ys])
        num_too_close = sum([x < border_thresh for x in dist_to_border])
        return num_too_close >= 2


    def expandRoi (self, roi, imwidth, imheight):
        deltay = (roi[2] - roi[0]) * self.expand_perc / 2
        deltax = (roi[3] - roi[1]) * self.expand_perc / 2
        roi[0] = max(roi[0] - deltay, 0)
        roi[1] = max(roi[1] - deltax, 0)
        roi[2] = min(roi[2] + deltay, imheight - 1)
        roi[3] = min(roi[3] + deltax, imwidth - 1)
        roi = [int(x) for x in roi]
        assert (roi[2] - roi[0] > 1 and roi[3] - roi[1] > 1)
        return roi

    
    def expandRoiFloat (self, roi, (imheight, imwidth), (perc_y, perc_x)):
        ''' Expand each side by given perc, float to stay within borders '''
        half_delta_y = float(roi[2] + 1 - roi[0]) * perc_y / 2
        half_delta_x = float(roi[3] + 1 - roi[1]) * perc_x / 2
        # expand each side
        roi[0] -= half_delta_y
        roi[1] -= half_delta_x
        roi[2] += half_delta_y
        roi[3] += half_delta_x
        # make integer
        roi = [int(x) for x in roi]
        # move to clip into borders
        if roi[0] < 0:
            roi[2] += abs(roi[0])
            roi[0] = 0
        if roi[1] < 0:
            roi[3] += abs(roi[1])
            roi[1] = 0
        if roi[2] > imheight-1:
            roi[0] -= abs((imheight-1) - roi[2])
            roi[2] = imheight-1
        if roi[3] > imwidth-1:
            roi[1] -= abs((imwidth-1) - roi[3])
            roi[3] = imwidth-1
        # check that now averything is within borders (bbox is not too big)
        assert (roi[0] >= 0 and roi[1] >= 0)
        assert (roi[2] <= imheight-1 and roi[3] <= imwidth-1)
        return roi


    def expandRoiToRatio (self, roi, (imheight, imwidth)):
        ''' Match ratio height to width. 
            The biggest side may not be increased '''
        # adjust width and height to ratio
        height = float(roi[2] + 1 - roi[0])
        width  = float(roi[3] + 1 - roi[1])
        if height / width < self.ratio:
           perc = self.ratio * width / height - 1
           roi = self.expandRoiFloat (roi, (imheight, imwidth), (perc, 0))
        else:
           perc = height / width / self.ratio - 1
           roi = self.expandRoiFloat (roi, (imheight, imwidth), (0, perc))
        # additional expansion
        perc = self.expand_perc - perc
        if perc > 0:
            roi = self.expandRoiFloat (roi, (imheight, imwidth), (perc, perc))
        return roi


    def assignOrientation (self, car):
        bc = car.getBottomCenter()
        car.yaw   = self.yaw_map   [bc[0], bc[1]]
        car.pitch = self.pitch_map [bc[0], bc[1]]
        return car




class FrameAnalyzer (BaseAnalyzer):

    def __init__(self):
        self.parser = FrameParser()

    def processImage (self, folder, annotation_file):

        tree = ET.parse(OP.join(self.labelme_data_path, 'Annotations', folder, annotation_file))

        # image, backimage, and ghost
        img = self.imageOfAnnotation (tree.getroot())
        assert (img.shape == self.backimage.shape)
        ghostimage = image2ghost (img, self.backimage)
        height, width, depth = img.shape

        cars = []

        for object_ in tree.getroot().findall('object'):

            # find the name of object. Filter all generic objects
            cartype = self.parser.parse(object_.find('name').text)
            if cartype == 'object':
                logging.info('skipped an "object"')
                continue
            if cartype is None:
                logging.info('skipped a None')
                continue

            # get all the points
            xs, ys = self.pointsOfPolygon(object_)

            # filter bad ones
            if self.isDegeneratePolygon(xs, ys): 
                logging.info ('degenerate polygon ' + str(xs) + ', ' + str(ys))
                continue
            if self.isPolygonAtBorder(xs, ys, width, height): 
                logging.info ('border polygon ' + str(xs) + ', ' + str(ys))
                continue

            # expand bbox
            roi = [min(ys), min(xs), max(ys), max(xs)]
            roi = self.expandRoiToRatio (roi, (height, width))
            assert (roi[2] - roi[0] > 1 and roi[3] - roi[1] > 1)

            # extract patch
            patch = img [roi[0]:roi[2]+1, roi[1]:roi[3]+1]
            ghost = ghostimage [roi[0]:roi[2]+1, roi[1]:roi[3]+1]

            # make and add car object to cars
            car = Car (roi2bbox(roi))
            car.patch = patch
            car.ghost = ghost
            car.name = cartype
            #car.source = folder  # dataset source
            car = self.assignOrientation(car)
            cars.append (car)

            # display
            #cv2.imshow('patch', patch)
            #cv2.imshow('ghost', ghost)
            #cv2.waitKey()

        if not cars: logging.warning ('file has no valid polygons: ' + annotation_file)
        return cars




#
# returns an array of tuples of form (car, car), or (car, None), or (None, car)
#
class PairAnalyzer (BaseAnalyzer):

    def __init__(self):
        self.parser = PairParser()

    def __bypartiteMatch (self, captions_t, captions_b, cars_t, cars_b, file_name):
        pairs = []

        # for every element in top list find its match in the bottom list
        for caption in captions_t:

            indices_t = [x for x, y in enumerate(captions_t) if y == caption]
            if len(indices_t) > 1:
                logging.error ('duplicates "' + str(caption) + '" on top in: ' + file_name)
                continue

            indices_b = [x for x, y in enumerate(captions_b) if y == caption]
            if len(indices_b) > 1:
                logging.error ('duplicates "' + str(caption) + '" on bottom in: ' + file_name)
                continue

            assert (len(indices_t) <= 1 and len(indices_b) <= 1)
            if indices_t and indices_b:
                logging.debug ('a valid pair "' + str(caption) + '" in: ' + file_name)
                car_pair = (cars_t[indices_t[0]], cars_b[indices_b[0]])
                captions_b[indices_b[0]] = None
            elif indices_t and not indices_b:
                logging.debug ('a valid top "' + str(caption) + '" in: ' + file_name)
                car_pair = (cars_t[indices_t[0]], None)

            pairs.append(car_pair)

        # collect the rest from the bottom list
        for caption in captions_b:
            if caption is None: continue

            indices_b = [x for x, y in enumerate(captions_b) if y == caption]
            if len(indices_b) > 1:
                logging.error ('duplicates "' + str(caption) + '" on bottom in: ' + file_name)
                continue

            if caption:
                logging.debug ('a valid bottom "' + str(caption) + '" in: ' + file_name)
                car_pair = (None, cars_b[indices_b[0]])
                pairs.append(car_pair)

        return pairs


    def processImage (self, folder, annotation_file):

        tree = ET.parse(OP.join(self.labelme_data_path, 'Annotations', folder, annotation_file))

        # image, backimage, and ghost
        halfheight, width, depth = self.backimage.shape
        img = self.imageOfAnnotation (tree.getroot())
        img_t = img[:halfheight, :]
        img_b = img[halfheight:, :]
        assert (img_t.shape == (halfheight, width, depth))
        assert (img_b.shape == (halfheight, width, depth))
        ghostimage_t = image2ghost (img_t, self.backimage)
        ghostimage_b = image2ghost (img_b, self.backimage)

        objects = tree.getroot().findall('object')
        captions_t = []
        captions_b = []
        cars_t = []
        cars_b = []

        # collect captions and assign statuses accordingly
        for object_ in objects:

            # get all the points
            xs, ys = self.pointsOfPolygon(object_)

            # filter bad ones
            if self.isDegeneratePolygon(xs, ys): 
                logging.info ('degenerate polygon ' + str(xs) + ', ' + str(ys))
                continue

            # bbox operations
            is_top = np.mean(np.mean(ys)) < halfheight
            if is_top:
                roi = [min(ys), min(xs), max(ys), max(xs)]
                img = img_t
                ghostimage = ghostimage_t
            else:
                roi = [min(ys)-halfheight, min(xs), max(ys)-halfheight, max(xs)]
                img = img_b
                ghostimage = ghostimage_b

            roi = self.expandRoiToRatio (roi, (halfheight, width))
            assert (roi[2] - roi[0] > 1 and roi[3] - roi[1] > 1)

            # extract patch
            patch = img [roi[0]:roi[2]+1, roi[1]:roi[3]+1]
            ghost = ghostimage [roi[0]:roi[2]+1, roi[1]:roi[3]+1]

            # find the name of object. Filter all generic objects
            (name, number) = self.parser.parse(object_.find('name').text)
            if name is None or number is None:
                logging.info('skipped a None')
                continue

            # make a car
            car = Car (roi2bbox(roi))
            car.patch = patch
            car.ghost = ghost
            car.name = name # name from the captions
            car = self.assignOrientation(car)

            # write to either top or bottom stack
            if is_top:
                captions_t.append((name, number))
                cars_t.append (car)
            else:
                captions_b.append((name, number))
                cars_b.append (car)

            # display
            #cv2.imshow('patch', patch)
            #cv2.imshow('ghost', ghost)
            #cv2.waitKey()

        pairs = self.__bypartiteMatch (captions_t, captions_b, cars_t, cars_b, annotation_file)

        if not pairs: logging.warning ('file has no valid polygons: ' + annotation_file)
        return pairs








if __name__ == '__main__':
    ''' Demo '''

    if os.environ.get('CITY_DATA_PATH') is None:
        print 'First please set the environmental variable CITY_DATA_PATH'
        sys.exit
    else:
        CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')

    FORMAT = '%(asctime)s %(levelname)s: \t%(message)s'
    logging.basicConfig (format=FORMAT, level=logging.INFO)

    labelme_data_path = OP.join(CITY_DATA_PATH, 'labelme')
    backimage_path = OP.join(CITY_DATA_PATH, 'camdata/cam572/5pm/models/backimage.png')
    geom_maps_dir = OP.join(CITY_DATA_PATH, 'models/cam572/')

    analyzer = FrameAnalyzer()
    analyzer.setPaths (labelme_data_path, backimage_path, geom_maps_dir)
    cars = analyzer.processImage('cam572-bright-frames', '000000.xml')

    