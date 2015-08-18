import abc
import numpy as np
import cv2
import os, sys
import os.path as op
import logging
import helperSetup


class ProcessorBase (object):
    ''' Declaration of interface functions '''

    @abc.abstractmethod
    def imread (self):
        __metaclass__ = abc.ABCMeta
        return

    @abc.abstractmethod
    def maskread (self):
        __metaclass__ = abc.ABCMeta
        return



class ProcessorImagefile (ProcessorBase):
    ''' 
    Implementation based on Image <-> Imagefile
    '''

    def __init__ (self, params = {}):
        helperSetup.setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
        self.relpath = params['relpath']
        self.image_cache = {}   # cache of previously read image(s)
        self.mask_cache = {}    # cache of previously read mask(s)

    def readImageImpl (self, image_id):
        imagepath = op.join (self.relpath, image_id)
        if not op.exists (imagepath):
            raise Exception ('ProcessorImagefile: image does not exist at path: "%s"' % imagepath)
        img = cv2.imread(imagepath)
        if img is None:
            raise Exception ('ProcessorImagefile: image file exists, but failed to read it')
        return img

    def writeImageImpl (self, image, image_id):
        imagepath = op.join (self.relpath, image_id)
        if image is None:
            raise Exception ('ProcessorImagefile: image to write is None')
        if not op.exists (op.dirname(imagepath)):
            os.makedirs (op.dirname(imagepath))
        cv2.imwrite (imagepath, image)

    def imread (self, image_id):
        if image_id in self.image_cache: 
            logging.debug ('ProcessorImagefile.imread: found image in cache')
            return self.image_cache[image_id]  # get cached image if possible
        image = self.readImageImpl (image_id)
        logging.debug ('ProcessorImagefile.imread: new image, updating cache')
        self.image_cache = {image_id: image}   # currently only 1 image in the cache
        return image

    def maskread (self, mask_id):
        if mask_id in self.mask_cache: 
            logging.debug ('ProcessorImagefile.maskread: found mask in cache')
            return self.mask_cache[mask_id]  # get cached mask if possible
        mask = self.readImageImpl (mask_id)
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        logging.debug ('ProcessorImagefile.imread: new mask, updating cache')
        self.mask_cache = {mask_id: mask}   # currently only 1 image in the cache
        return mask

    def imwrite (self, image, image_id):
        assert len(image.shape) == 3 and image.shape[2] == 3
        self.writeImageImpl (image, image_id)

    def maskwrite (self, mask, mask_id):
        assert len(mask.shape) == 2
        self.writeImageImpl (mask, mask_id)



class ProcessorFolder (ProcessorBase):
    '''
    Implementation based on Image <-> (Dataset, Id)
      'dataset' is a directory with images
      'image_id' is a name of image in that folder
    '''

    def __init__ (self, params):
        helperSetup.setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
        self.relpath = params['relpath']
        self.image_cache = {}   # cache of previously read image(s)
        self.mask_cache = {}    # cache of previously read mask(s)

    def readImageImpl (self, name, dataset):
        imagepath = op.join (self.relpath, dataset, name)
        if not op.exists (imagepath):
            raise Exception ('ProcessorFolder: image does not exist at path: "%s"' % imagepath)
        img = cv2.imread(imagepath)
        if img is None:
            raise Exception ('ProcessorFolder: image file exists, but failed to read it')
        return img

    def writeImageImpl (self, image, name, dataset):
        imagepath = op.join (self.relpath, dataset, name)
        if image is None:
            raise Exception ('ProcessorFolder: image to write is None')
        if not op.exists (op.dirname(imagepath)):
            os.makedirs (op.dirname(imagepath))
        cv2.imwrite (imagepath, image)

    def imread (self, image_id, dataset):
        unique_id = (image_id, dataset)
        if unique_id in self.image_cache: 
            logging.debug ('ProcessorFolder.imread: found image in cache')
            return self.image_cache[unique_id]  # get cached image if possible
        image = self.readImageImpl ('%06d.jpg' % image_id, dataset) # image names are 6-digits
        logging.debug ('ProcessorFolder.imread: new image, updating cache')
        self.image_cache = {unique_id: image}   # currently only 1 image in the cache
        return image

    def maskread (self, mask_id, dataset):
        unique_id = (mask_id, dataset)
        if unique_id in self.mask_cache: 
            logging.debug ('ProcessorFolder.maskread: found mask in cache')
            return self.mask_cache[unique_id]  # get cached image if possible
        mask = self.readImageImpl ('%06d.png' % mask_id, dataset) # mask names are 6-digits
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        logging.debug ('ProcessorFolder.maskread: new mask, updating cache')
        self.mask_cache = {unique_id: mask}   # currently only 1 image in the cache
        return mask

    def imwrite (self, image, image_id, dataset):
        assert len(image.shape) == 3 and image.shape[2] == 3
        self.writeImageImpl (image, '%06d.jpg' % image_id, dataset)

    def maskwrite (self, mask, mask_id, dataset):
        assert len(mask.shape) == 2
        self.writeImageImpl (mask, '%06d.png' % mask_id, dataset)



class ProcessorRandom (ProcessorBase):
    '''
    Generate a random image for unittests in different modules
    Currently both 'imread' and 'maskread' interface is compatible with ProcessorImagefile
    '''    

    def __init__ (self, params):
        helperSetup.assertParamIsThere (params, 'dims')
        self.dims = params['dims']

    def imread (self, image_id = None):
        (height, width) = self.dims
        return np.ones ((height, width, 3), dtype=np.uint8) * 128

    def maskread (self, mask_id = None):
        ''' Generate a 2x2 checkerboard '''
        (height, width) = self.dims
        mask = np.zeros (self.dims, dtype=np.uint8)
        mask[0:height/2, 0:width/2] = 255
        mask[height/2:height, width/2:width] = 255
        return mask

    def imwrite (self, image, image_id = None):
        assert len(image.shape) == 3 and image.shape[2] == 3 and image.shape[0:2] == self.dims
        return

    def maskwrite (self, mask, mask_id = None):
        assert len(mask.shape) == 2 and mask.shape == self.dims
        return
