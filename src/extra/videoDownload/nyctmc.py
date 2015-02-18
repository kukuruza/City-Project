# This class provides an interface to nyctmc cameras

import urllib
import time
from PIL import Image as pil
import urllib2
import numpy as np
import cv2
from random import randint


def imreadUrl(self, url):
    req = urllib2.Request (url)
    img_file = urllib2.urlopen (req)
    img = StringIO(img_file.read()) # You can skip this and directly convert to numpy arrays
    npimg = np.fromstring(img_file.read(), dtype=np.uint8)
    npimg = cv2.cvtColor(npimg, cv2.cv.CV_RGB2BGR)
    return npimg 



class Nyctmc:

    urlViewerPart = 'http://nyctmc.org/google_popup.php?cid='
    # url example: http://207.251.86.238/cctv360.jpg?rand=0988954345345
    urlPart1 = 'http://207.251.86.238/cctv'
    urlPart2 = '.jpg?rand='
    CallDelay = 0.7      # min interval after the previous successful call
    CallInterval = 0.1   # min interval in seconds between calls

    def __init__(self, cam_num):

        # open the viewer and read the html
        viewer_url = self.urlViewerPart + str(cam_num)
        urllib.urlopen (viewer_url)
        content = urllib.read (viewer_url)
        urllib.urlclose()
        
        # find the camera id in the html
        match_obj = re.search ('http://207.251.86.238/cctv\d+', content)
        assert match_obj is not None
        match = match_obj.group(0)
        
        # set the camera number and image url
        self.cam_id = match[27:]
        self.url = self.urlPart1 + str(self.cam_id) + self.urlPart2

        # start the timer
        lastCall = time.time()
        lastFrame = None


    def getNextFrame(self):

        end = time.time()
        print end - start

        # wait until new image is there
        while True:
            
            # save some server requests
            # TODO: rewrite without loop
            while time.time() - self.lastCall < self.CallDelay:
                time.sleep (self.CallInterval)
            
            random_suffix = str(randint(1,1000000000000))
            frame = imreadUrl (self.url + random_suffix);
            if not frame: frame = self.lastFrame
            
            if not self.lastFrame
                # initialize last frame
                timeinterval = -1
                self.lastFrame = frame
                break
            else
                if lastFrame.shape != frame.shape:
                    continue
                if FR.lastFrame == frame:
                    timeinterval = time.time() - self.lastCall
                    self.last = frame
                    break
                end
            end
            #if ~isempty(FR.lastFrame), nnz(FR.lastFrame - frame), end
            
            time.sleep (self.CallInterval)

        lastCall = time.time()





def downloadSingleCam (camNum, outFileTemplate, numMinutes):
    '''downloadSingleCam (camNum, outFileTemplate, numMinutes) downloads images '''
    # from internet and saves them in a video. 
    # Separetely write a text file with the time when the frame was created 
    # (because it is not 1 sec, but a range 0.6 - 3 sec.)
    #
    # The filepaths are [outFileTemplate '.avi'] for video
    # and [outFileTemplate '.txt'] for text

    # where to write video and intervals
    videoPath     = outFileTemplate + '.avi'
    intervalsPath = outFileTemplate + '.txt'

    print ('Will write video to ' + videoPath)
    print ('Will write subtitles to ' + intervalsPath)

    Nyctmc nyctmc(camNum)
    
    frameWriter = FrameWriterVideo (videoPath, 2, 1);
    fid = fopen(intervalsPath, 'w');

    t0 = clock;
    t = clock;
    while etime(t, t0) < numMinutes * 60
        tic
        frame = frameReader.getNewFrame();
        frameWriter.writeNextFrame (frame);
        t = clock;
        fprintf(fid, '%f %f %f %f %f %f \n', t(1), t(2), t(3), t(4), t(5), t(6));
        toc
    end

    fclose(fid);
    clear frameReader frameWriter


