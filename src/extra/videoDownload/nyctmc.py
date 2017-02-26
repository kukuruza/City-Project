import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
import logging
import copy
import re
import urllib
import datetime, time
from cStringIO import StringIO
from PIL import Image, ImageChops
import urllib2
import numpy as np
import cv2
from random import randint
from helperSetup import setupLogging, atcity


#def imreadUrl(self, url):
#    req = urllib2.Request (url)
#    img_file = urllib2.urlopen (req)
#    img = StringIO(img_file.read()) # You can skip this and directly convert to numpy arrays
#    npimg = np.fromstring(img_file.read(), dtype=np.uint8)
#    npimg = cv2.cvtColor(npimg, cv2.cv.CV_RGB2BGR)
#    return npimg 

def is_similar(image1, image2):
    return image1.shape == image2.shape and not(np.bitwise_xor(image1,image2).any())

class Nyctmc:

    urlViewerPart = 'http://nyctmc.org/google_popup.php?cid='
    # url example: http://207.251.86.238/cctv360.jpg?rand=0988954345345
    urlPart1 = 'http://207.251.86.238/cctv'
    urlPart2 = '.jpg?rand='
    CallDelay = 1.0      # min interval after the previous successful call
    CallInterval = 0.1   # min interval in seconds between calls

    def __init__(self, cam_num):

        # open the viewer and read the html
        viewer_url = self.urlViewerPart + str(cam_num)
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

        # wait until new image is there
        while True:
            
            # save some server requests
            # TODO: rewrite without loop
            while time.time() - self.lastCall < self.CallDelay:
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
                assert (self.last_str is not None)
                self.img_str = self.last_str
            
            # if it is the first frame
            if self.last_str is None:
                logging.debug ('initialized the first frame')
                self.last_str = self.img_str
                break
            else:
                if self.last_str.getvalue() != self.img_str.getvalue():
                    # condition to quit the while loop
                    logging.debug ('frame updated')
                    self.last_str = self.img_str
                    break
                else:
                    logging.debug ('still the same')

            time.sleep (self.CallInterval)

        lastCall = time.time()
        frame = Image.open (self.img_str).convert("RGB")
        return frame





def downloadSingleCam (camNum, outFileTemplate, numMinutes):
    '''downloadSingleCam (camNum, outFileTemplate, numMinutes) downloads images
       from internet and saves them in a video. 
       Separetely write a text file with the time when the frame was created 
       (because it is not 1 sec, but a range 0.6 - 3 sec.)
  
       The filepaths are [outFileTemplate '.avi'] for video
       and [outFileTemplate '.txt'] for text
    '''

    # where to write video and intervals
    videoPath     = aticty(outFileTemplate + '.avi')
    intervalsPath = atcity(outFileTemplate + '.txt')

    logging.info ('Will write video to ' + videoPath)
    logging.info ('Will write subtitles to ' + intervalsPath)

    fps = 2
    fourcc = cv2.cv.CV_FOURCC(*'mp4v')

    nyctmc = Nyctmc (camNum)
    f = open(intervalsPath, 'w')

    from subprocess import Popen, PIPE
    #p = Popen(['ffmpeg', '-y', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-r', '25', 
    #     '-i', '-', '-vcodec', 'mpeg4', '-q:v', '25', '-vf', 'fps=fps=2', videoPath], stdin=PIPE)

    writer = None

    t0 = time.time()
    t = t0
    while t - t0 < numMinutes * 60:
        frame = nyctmc.getNextFrame()
        if frame is None:
            raise Exception ('returned a None frame')

        im = np.array(frame, dtype=np.uint8)
        im = cv2.cvtColor(im, cv2.cv.CV_RGB2BGR)

        if not writer:
            logging.info ('set up writer')
            (height, width, depth) = im.shape
            assert (depth == 3)
            writer = cv2.VideoWriter (videoPath, fourcc, fps, (width, height), 1 )

        writer.write(im)

        #frame.save(p.stdin, 'JPEG')
        t1 = t
        t = time.time()
        logging.info ('wrote frame at second: ' + str(t - t1))



    f.close();

    cv2.destroyAllWindows()

    #p.stdin.close()
    #p.wait()

    #writer.release()
    del (writer)




if __name__ == '__main__':

    setupLogging ('log/io/nyctmc.log', logging.DEBUG)

    downloadSingleCam (578, 'data/camdata/test', 1)

