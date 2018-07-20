import os, sys, os.path as op
import abc
import numpy as np
import scipy.misc
import cv2
import logging
from pkg_resources import parse_version
from helperSetup import atcity, atcitydata


# returns OpenCV VideoCapture property id given, e.g., "FPS"
def capPropId(prop):
  OPCV3 = parse_version(cv2.__version__) >= parse_version('3')
  return getattr(cv2 if OPCV3 else cv2.cv, ("" if OPCV3 else "CV_") + "CAP_PROP_" + prop)

def getVideoLength(video_cv2):
  return video_cv2.get(capPropId('FRAME_COUNT'))

# These are thin wrappers around scipy.misc
# The goal is to move gradually from cv2 to scipy.misc,
#   and these function keep compatibility in channel order

def imread(impath):
  im = scipy.misc.imread(impath)
  if len(im.shape) == 3 and im.shape[2] == 3:
    im = im[:,:,[2,1,0]]
  elif len(im.shape) == 3 and im.shape[2] == 4:
    im = im[:,:,[2,1,0,3]]
  return im

def imsave(impath, im):
  if len(im.shape) == 3 and im.shape[2] == 3:
    im = im[:,:,[2,1,0]]
  scipy.misc.imsave(atcity(impath), im)


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

    def __init__ (self, relpath=None):
        self.relpath = relpath
        if self.relpath is not None:
            logging.info('ReaderVideo: relpath is set to %s' % self.relpath)
        else:
            logging.debug('ReaderVideo: relpath is NOT set.')
        self.image_cache = {}    # cache of previously read image(s)
        self.mask_cache = {}     # cache of previously read mask(s)
        self.image_video = {}    # map from image video name to VideoCapture object
        self.mask_video = {}     # map from mask  video name to VideoCapture object

    def _openVideoCapture_ (self, videofile):
        ''' Open video and set up bookkeeping '''
        logging.debug ('opening video: %s' % videofile)
        if self.relpath is not None:
          videopath = op.join(self.relpath, videofile)
          logging.debug('Videopath is relative to the provided relpath: %s' % videopath)
        elif op.exists(atcity(videofile)):
          videopath = atcity(videofile)
          logging.debug('Videopath is relative to CITY_PATH: %s' % videopath)
        elif op.exists(atcitydata(videofile)):
          videopath = atcitydata(videofile)
          logging.warning('Deprecated video path relative to CITY_DATA_PATH: %s' % videopath)
        else:
          raise Exception('videofile does not exist: %s' % videofile)
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
          if frame_id >= video_dict[videopath].get(capPropId('FRAME_COUNT')):
            raise ValueError('frame_id %d exceeds the video length' % frame_id)
          else:
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
        if mask_id is None:
            return None
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

    def __init__ (self, out_dataset):
        super(ProcessorVideo, self).__init__()
        self.out_dataset = out_dataset
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

        logging.info ('opening video: %s' % videofile)
        videopath = atcity (videofile)
        assert not op.exists (videopath), \
            'Video already exists at %s. Is it a mistake?' % videopath
        assert op.exists(op.dirname(videopath)), \
            'Video directory does not exist at %s. Is it a mistake?' % op.dirname(videopath)
        handler = cv2.VideoWriter (videopath, fourcc, fps, frame_size, isColor=True)#not ismask)
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
        if mask.dtype == bool:
          mask = mask.copy().astype(np.uint8) * 255

        return self.writeImpl (mask, mask_id, ismask=True)

    def close (self):
        for video in self.out_mask_video.itervalues():
            video.release()
        for video in self.out_mask_video.itervalues():
            video.release()


# TODO: need unit tests
class SimpleWriter:

  def __init__(self, vimagefile=None, vmaskfile=None, unsafe=False):
    self.unsafe  = unsafe
    self.vimagefile = vimagefile
    self.vmaskfile = vmaskfile
    self.image_writer = None
    self.mask_writer = None
    self.image_current_frame = -1
    self.mask_current_frame = -1
    self.frame_size = None        # used for checks


  def _openVideoWriter_ (self, ref_frame, ismask):
    ''' open a video for writing with parameters from the reference video (from reader) '''
    fps = 2
    fourcc = 1196444237
    width  = ref_frame.shape[1]
    height = ref_frame.shape[0]
    if self.frame_size is None:
      self.frame_size = (width, height)
    else:
      assert self.frame_size == (width, height), \
         'frame_size different for image and mask: %s vs %s' % \
         (self.frame_size, (width, height))

    vfile = self.vmaskfile if ismask else self.vimagefile
    logging.info ('SimpleWriter: opening video: %s' % vfile)
    
    # check if video exists
    vpath = atcity(vfile)
    if op.exists (vpath):
      if self.unsafe:
        os.remove(vpath)
      else:
        raise Exception('Video already exists: %s. A mistake?' % vpath)
        
    # check if dir exists
    if not op.exists(op.dirname(vpath)):
      if self.unsafe:
        os.makedirs(op.dirname(vpath))
      else:
        raise Exception('Video dir does not exist: %s. A mistake?' % op.dirname(vpath))

    handler = cv2.VideoWriter (vpath, fourcc, fps, self.frame_size, isColor=True)#not ismask)
    if not handler.isOpened():
        raise Exception('video failed to open: %s' % videopath)
    if ismask:
        self.mask_writer  = handler
    else:
        self.image_writer = handler


  def imwrite (self, image):
    assert self.vimagefile is not None
    if self.image_writer is None:
      self._openVideoWriter_ (image, ismask=False)
    assert len(image.shape) == 3 and image.shape[2] == 3, image.shape
    # write
    assert (image.shape[1], image.shape[0]) == self.frame_size
    self.image_writer.write(image)
    # return recorded imagefile
    self.image_current_frame += 1
    return '%s/%06d' % (op.splitext(self.vimagefile)[0], self.image_current_frame)


  def maskwrite (self, mask):
    assert self.vmaskfile is not None
    assert len(mask.shape) == 2
    if self.mask_writer is None:
      self._openVideoWriter_ (mask, ismask=True)
    if mask.dtype == bool:
      mask = mask.copy().astype(np.uint8) * 255
    mask = np.stack((mask, mask, mask), axis=-1)  # Otherwise mask is not written well.
    # write
    assert len(mask.shape) == 3 and mask.shape[2] == 3, mask.shape
    assert (mask.shape[1], mask.shape[0]) == self.frame_size
    self.mask_writer.write(mask)
    # return recorded imagefile
    self.mask_current_frame += 1
    return '%s/%06d' % (op.splitext(self.vmaskfile)[0], self.mask_current_frame)


  def close (self):
    if self.image_writer is not None: 
      self.image_writer.release()
    if self.mask_writer is not None: 
      self.mask_writer.release()



class ProcessorImagefile (ProcessorBase):
    ''' 
    Implementation based on Image <-> Imagefile
    '''

    def __init__ (self):
        self.image_cache = {}   # cache of previously read image(s)
        self.mask_cache = {}    # cache of previously read mask(s)

    def readImpl (self, image_id):
        imagepath = op.join (os.getenv('CITY_PATH'), image_id)
        logging.debug ('imagepath: %s' % imagepath)
        if not op.exists (imagepath):
            raise Exception ('image does not exist at path: "%s"' % imagepath)
        img = cv2.imread(imagepath)
        if img is None:
            raise Exception ('image file exists, but failed to read it')
        return img

    def writeImpl (self, image, image_id):
        imagepath = op.join (os.getenv('CITY_PATH'), image_id)
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


