import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
import logging
import re
import datetime, time
from cStringIO import StringIO
from PIL import Image, ImageChops
import urllib2
import numpy as np
from random import randint
from helperSetup import setupLogging, atcity
from helperDb import makeTimeString


#def imreadUrl(self, url):
#    req = urllib2.Request (url)
#    img_file = urllib2.urlopen (req)
#    img = StringIO(img_file.read()) # You can skip this and directly convert to numpy arrays
#    npimg = np.fromstring(img_file.read(), dtype=np.uint8)
#    npimg = cv2.cvtColor(npimg, cv2.cv.CV_RGB2BGR)
#    return npimg 

class FrameReader:

  IsBGR = True

  urlViewerPart = 'http://dotsignals.org/google_popup.php?cid='
  # url example: http://207.251.86.238/cctv360.jpg?rand=0988954345345
  urlPart1 = 'http://207.251.86.238/cctv'
  urlPart2 = '.jpg?rand='
  CallDelay = 1.0      # min interval after the previous successful call
  CallInterval = 0.1   # min interval in seconds between calls

  def __init__(self, cam_num):

    # open the viewer and read the html
    viewer_url = self.urlViewerPart + str(cam_num)
    logging.debug(viewer_url)
    response = urllib2.urlopen (viewer_url)
    content = response.read()
    response.close()

    # find the camera id in the html
    match_obj = re.search ('http://207.251.86.238/cctv\d+', content)
    assert match_obj is not None
    match = match_obj.group(0)
    
    # set the camera number and image url
    self.cam_id = match[26:]                  # !!! index is different from matlab 
    logging.info ('match: ' + str(match))
    self.url = self.urlPart1 + str(self.cam_id) + self.urlPart2
    logging.info ('url part for this camera is: ' + self.url)

    # start the timer
    self.lastCall = time.time()
    self.last_str = None
    self.img_str = None


  def getNextFrame(self):

    def _decode_image_str(img_str):
      try:
        frame = Image.open (self.img_str).convert("RGB")
        frame = np.array(frame)
        return frame
      except:
        logging.warning ('cannot decode jpeg image')
        return None

    # wait self.CallDelay since the last successful call
    leftToSleep = self.CallDelay - (time.time() - self.lastCall)
    if leftToSleep > 0:
      time.sleep (leftToSleep)
    
    # work until new image is there
    while True:
      time.sleep (self.CallInterval)
      
      random_suffix = str(randint(1,1000000000000))

      try:
        response = urllib2.urlopen (self.url + random_suffix, timeout=1)
        self.img_str = StringIO (response.read())
        response.close()
        logging.debug ('read frame')
      except:
        logging.warning ('exception at reading url')
        time.sleep (self.CallInterval)
        continue 

      # that's possible
      if self.img_str is None: 
        logging.warning ('frame was None')
        continue
      
      # if it is the first frame
      if self.last_str is None:
        logging.debug ('initialized the first frame')
        frame = _decode_image_str(self.img_str)
        if frame is None: 
          continue
        break

      # check if the new image string is different from previous
      if self.last_str.getvalue() == self.img_str.getvalue():
        logging.debug ('still the same')
        continue

      # check that the image is valid
      frame = _decode_image_str(self.img_str)
      if frame is None: 
        logging.warning ('cannot decode jpeg image')
        continue
      else:
        break

    if not self.IsBGR:
      frame = frame[:,:,[2,1,0]]

    logging.info ('frame updated in %s sec.' % str(time.time() - self.lastCall))
    self.last_str = self.img_str
    self.lastCall = time.time()

    return frame, datetime.datetime.now()





if __name__ == '__main__':

    setupLogging ('log/io/FrameReaderInternet.log', logging.DEBUG)

    reader = FrameReader(578)

    import cv2
    while True:
      frame, timestamp = reader.getNextFrame()
      print makeTimeString(timestamp)
      cv2.imshow('test', frame)
      cv2.waitKey(10)

