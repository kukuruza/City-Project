import os, sys, os.path as op
import abc
import numpy as np
import cv2
import logging
from pkg_resources import parse_version
from helperSetup import setParamUnlessThere, assertParamIsThere


# returns OpenCV VideoCapture property id given, e.g., "FPS"
def capPropId(prop):
    OPCV3 = parse_version(cv2.__version__) >= parse_version('3')
    return getattr(cv2 if OPCV3 else cv2.cv, ("" if OPCV3 else "CV_") + "CAP_PROP_" + prop)


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

    @abc.abstractmethod
    def close (self):
        __metaclass__ = abc.ABCMeta
        return


class ReaderVideo (ProcessorBase):
    '''
    Implementation based on Image <-> Frame in video.
    OpenCV VideoCapture allows random access to frames!
    When we want to access a frame from matlab it's more complicated, 
      but usually we don't need random access to frames anyway, just the next one.
      Also, let's have a cache of a few previously read frames
    '''

    def __init__ (self, params = {}):
        setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
        self.relpath = params['relpath']
        self.image_cache = {}    # cache of previously read image(s)
        self.mask_cache = {}     # cache of previously read mask(s)
        self.image_video = {}    # map from image video name to VideoCapture object
        self.mask_video = {}     # map from mask  video name to VideoCapture object

    def _openVideoCapture_ (self, videopath):
        ''' Open video and set up bookkeeping '''
        logging.info ('opening video: %s' % videopath)
        videopath = op.join (self.relpath, videopath)
        if not op.exists (videopath):
            raise Exception('videopath does not exist: %s' % videopath)
        handle = cv2.VideoCapture(videopath)  # open video
        if not handle.isOpened():
            raise Exception('video failed to open: %s' % videopath)
        return handle

    def readImpl (self, image_id, ismask):
        # choose the dictionary, depending on whether it's image or mask
        video_dict = self.image_video if ismask else self.mask_video
        # video id set up
        videopath = op.dirname(image_id) + '.avi'
        if videopath not in video_dict:
            video_dict[videopath] = self._openVideoCapture_ (videopath)
        # frame id
        frame_name = op.basename(image_id)
        frame_id = int(filter(lambda x: x.isdigit(), frame_name))  # number
        logging.debug ('from image_id %s, got frame_id %d' % (image_id, frame_id))
        # read the frame
        video_dict[videopath].set(capPropId('POS_FRAMES'), frame_id)
        retval, img = video_dict[videopath].read()
        if not retval:
            raise Exception('could not read image_id %s' % image_id)
        # assign the dict back to where it was taken from
        if ismask: self.mask_video = video_dict 
        else: self.image_video = video_dict
        # and finally...
        return img

    def imread (self, image_id):
        if image_id in self.image_cache: 
            logging.debug ('imread: found image in cache')
            return self.image_cache[image_id]  # get cached image if possible
        image = self.readImpl (image_id, ismask=False)
        logging.debug ('imread: new image, updating cache')
        self.image_cache = {image_id: image}   # currently only 1 image in the cache
        return image

    def maskread (self, mask_id):
        if mask_id in self.mask_cache: 
            logging.debug ('maskread: found mask in cache')
            return self.mask_cache[mask_id]  # get cached mask if possible
        mask = self.readImpl (mask_id, ismask=True)
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        mask = mask > 127
        logging.debug ('imread: new mask, updating cache')
        self.mask_cache = {mask_id: mask}   # currently only 1 image in the cache
        return mask


class ProcessorVideo (ReaderVideo):
    '''
    Implementation based on Image <-> Frame in video.
    Unfortunately, the writing is sequential only, no random access

    Inherited from ProcessorVideoReader to ensure there's just one video dataset (temporary) 
      and to get parameters of the input video
    '''

    def __init__ (self, params = {}):
        super(ProcessorVideo, self).__init__(params)

        setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
        assertParamIsThere  (params, 'out_dataset')
        self.relpath = params['relpath']
        self.out_dataset = params['out_dataset']
        self.out_image_video = {}    # map from image video name to VideoWriter object
        self.out_mask_video = {}     # map from mask  video name to VideoWriter object
        self.out_current_frame = {}  # used to return imagefile and maskfile 
        self.frame_size = {}         # used for checks

    def _openVideoWriter_ (self, videofile, ref_video, ismask):
        ''' open a video for writing with parameters from the reference video (from reader) '''
        width  = int(ref_video.get(capPropId('FRAME_WIDTH')))
        height = int(ref_video.get(capPropId('FRAME_HEIGHT')))
        fourcc = int(ref_video.get(capPropId('FOURCC')))
        fps    =     ref_video.get(capPropId('FPS'))
        frame_size = (width, height)

        self.frame_size[videofile] = frame_size
        self.out_current_frame[videofile] = -1  # first write will turn in to 0

        logging.info ('opening video: %s' % videofile)
        videopath = op.join (self.relpath, videofile)
        assert not op.exists (op.join (self.relpath, videopath)), \
            'Video already exists at %s. Is it a mistake?' % op.join(self.relpath, videopath)
        assert op.exists(op.dirname(videopath)), \
            'Video directory does not exist at %s. Is it a mistake?' % op.dirname(videopath)
        handler = cv2.VideoWriter (videopath, fourcc, fps, frame_size, not ismask)
        if not handler.isOpened():
            raise Exception('video failed to open: %s' % videopath)
        if ismask:
            self.out_mask_video[videofile]  = handler
        else:
            self.out_image_video[videofile] = handler


    def writeImpl (self, image, image_id, ismask):
        # choose the dictionary, depending on whether it's image or mask
        in_video_dict = self.mask_video if ismask else self.image_video
        # input video id
        in_videopath = op.dirname(image_id) + '.avi'
        # write frame only if it has been read before
        logging.debug ('in_videopath: %s' % in_videopath)
        assert in_videopath in in_video_dict, 'in_videopath: %s' % in_videopath
        # write only from videos, where we have the rule to make output video name
        if in_videopath not in self.out_dataset:
            raise Exception ('video %s is not in out_dataset' % in_videopath)

        # choose the dictionary, depending on whether it's image or mask
        out_video_dict = self.out_mask_video if ismask else self.out_image_video
        # output video id
        out_videopath = self.out_dataset[in_videopath]
        logging.debug ('out_videopath: %s' % out_videopath)
        logging.debug ('input video %s translated to output %s' % (in_videopath, out_videopath))
        if out_videopath not in out_video_dict:
            self._openVideoWriter_ (out_videopath, in_video_dict[in_videopath], ismask)
        # choose the dictionary again, depending on whether it's image or mask
        out_video_dict = self.out_mask_video if ismask else self.out_image_video
        assert out_videopath in out_video_dict

        # Disabled because want to write from Nth from in augmentation/processScene.py
        # write the frame only if it is the next frame
        # frame_expected = self.out_current_frame[out_videopath] + 1
        # frame_actual  = int(filter(lambda x: x.isdigit(), op.basename(image_id)))  # number
        # if frame_actual != frame_expected:
        #     raise Exception('''Random access for writing is not supported now.
        #                        New frame is #%d, but the expected frame is #%d''' % 
        #                        (frame_actual, frame_expected))
        self.out_current_frame[out_videopath] += 1  # update

        # check frame size and write
        assert (image.shape[1], image.shape[0]) == self.frame_size[out_videopath]
        out_video_dict[out_videopath].write(image)

        # return imagefile / maskfile
        return op.join (op.splitext(out_videopath)[0], 
                        '%06d' % self.out_current_frame[out_videopath])

    def imwrite (self, image, image_id):
        '''Returns:  recorded imagefile'''
        assert len(image.shape) == 3 and image.shape[2] == 3
        return self.writeImpl (image, image_id, ismask=False)

    def maskwrite (self, mask, mask_id):
        assert len(mask.shape) == 2
        assert mask.dtype == bool
        mask = mask.copy().astype(np.uint8) * 255
        return self.writeImpl (mask, mask_id, ismask=True)

    def close (self):
        for video in self.out_mask_video.itervalues():
            video.release()
        for video in self.out_mask_video.itervalues():
            video.release()



class ProcessorImagefile (ProcessorBase):
    ''' 
    Implementation based on Image <-> Imagefile
    '''

    def __init__ (self, params = {}):
        setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
        self.relpath = params['relpath']
        self.image_cache = {}   # cache of previously read image(s)
        self.mask_cache = {}    # cache of previously read mask(s)

    def readImpl (self, image_id):
        imagepath = op.join (self.relpath, image_id)
        logging.debug ('imagepath: %s' % imagepath)
        if not op.exists (imagepath):
            raise Exception ('image does not exist at path: "%s"' % imagepath)
        img = cv2.imread(imagepath)
        if img is None:
            raise Exception ('image file exists, but failed to read it')
        return img

    def writeImpl (self, image, image_id):
        imagepath = op.join (self.relpath, image_id)
        if image is None:
            raise Exception ('image to write is None')
        if not op.exists (op.dirname(imagepath)):
            os.makedirs (op.dirname(imagepath))
        cv2.imwrite (imagepath, image)

    def imread (self, image_id):
        if image_id in self.image_cache: 
            logging.debug ('imread: found image in cache')
            return self.image_cache[image_id]  # get cached image if possible
        image = self.readImpl (image_id)
        logging.debug ('imread: new image, updating cache')
        self.image_cache = {image_id: image}   # currently only 1 image in the cache
        return image

    def maskread (self, mask_id):
        if mask_id in self.mask_cache: 
            logging.debug ('maskread: found mask in cache')
            return self.mask_cache[mask_id]  # get cached mask if possible
        mask = self.readImpl (mask_id)
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        mask = mask > 127
        logging.debug ('imread: new mask, updating cache')
        self.mask_cache = {mask_id: mask}   # currently only 1 image in the cache
        return mask

    def imwrite (self, image, image_id):
        assert len(image.shape) == 3 and image.shape[2] == 3
        self.writeImpl (image, image_id)

    def maskwrite (self, mask, mask_id):
        assert len(mask.shape) == 2
        assert mask.dtype == bool
        mask = mask.copy().astype(np.uint8) * 255
        self.writeImpl (mask, mask_id)

    def close (self): pass



class ProcessorFolder (ProcessorBase):
    '''
    Implementation based on Image <-> (Dataset, Id)
      'dataset' is a directory with images
      'image_id' is a name of image in that folder
    '''

    def __init__ (self, params = {}):
        setParamUnlessThere (params, 'relpath', os.getenv('CITY_DATA_PATH'))
        self.relpath = params['relpath']
        self.image_cache = {}   # cache of previously read image(s)
        self.mask_cache = {}    # cache of previously read mask(s)

    def readImpl (self, name, dataset):
        imagepath = op.join (self.relpath, dataset, name)
        if not op.exists (imagepath):
            raise Exception ('ProcessorFolder: image does not exist at path: "%s"' % imagepath)
        img = cv2.imread(imagepath)
        if img is None:
            raise Exception ('ProcessorFolder: image file exists, but failed to read it')
        return img

    def writeImpl (self, image, name, dataset):
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
        image = self.readImpl ('%06d.jpg' % image_id, dataset) # image names are 6-digits
        logging.debug ('ProcessorFolder.imread: new image, updating cache')
        self.image_cache = {unique_id: image}   # currently only 1 image in the cache
        return image

    def maskread (self, mask_id, dataset):
        unique_id = (mask_id, dataset)
        if unique_id in self.mask_cache: 
            logging.debug ('ProcessorFolder.maskread: found mask in cache')
            return self.mask_cache[unique_id]  # get cached image if possible
        mask = self.readImpl ('%06d.png' % mask_id, dataset) # mask names are 6-digits
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        mask = mask > 127
        logging.debug ('ProcessorFolder.maskread: new mask, updating cache')
        self.mask_cache = {unique_id: mask}   # currently only 1 image in the cache
        return mask

    def imwrite (self, image, image_id, dataset):
        assert len(image.shape) == 3 and image.shape[2] == 3
        self.writeImpl (image, '%06d.jpg' % image_id, dataset)

    def maskwrite (self, mask, mask_id, dataset):
        assert len(mask.shape) == 2
        self.writeImpl (mask, '%06d.png' % mask_id, dataset)

    def close (self): pass



class ProcessorRandom (ProcessorBase):
    '''
    Generate a random image for unittests in different modules
    Currently both 'imread' and 'maskread' interface is compatible with ProcessorImagefile
    '''    

    def __init__ (self, params):
        assertParamIsThere (params, 'dims')
        self.dims = params['dims']

    def imread (self, image_id = None):
        (height, width) = self.dims
        return np.ones ((height, width, 3), dtype=np.uint8) * 128

    def maskread (self, mask_id = None):
        ''' Generate a 2x2 checkerboard '''
        (height, width) = self.dims
        mask = np.zeros (self.dims, dtype=bool)
        mask[0:height/2, 0:width/2] = 255
        mask[height/2:height, width/2:width] = 255
        return mask

    def imwrite (self, image, image_id = None):
        assert len(image.shape) == 3 and image.shape[2] == 3 and image.shape[0:2] == self.dims
        return

    def maskwrite (self, mask, mask_id = None):
        assert len(mask.shape) == 2 and mask.shape == self.dims
        return

    def close (self): pass

