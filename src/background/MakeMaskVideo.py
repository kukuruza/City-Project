import logging
import numpy as np
import cv, cv2
import sys, os, os.path as op
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
import helperSetup


def makeMaskVideo (in_image_videopath, out_mask_videopath, params = {}):
    '''
    Use GMM model to extract foreground mask from 'in_image_videopath'.
    Save the masks as a video 'out_mask_videopath'.
    '''
    logging.info ('==== makeMaskVideo ====')
    helperSetup.setParamUnlessThere (params, 'write', True)
    helperSetup.setParamUnlessThere (params, 'show', False)
    print 'write: %s' % params['write']

    # init GMM model
    fgbg = cv2.BackgroundSubtractorMOG (10, 3, 0.95)
    #fgbg = cv2.BackgroundSubtractorMOG2 (1, 100, True)

    inVideo  = cv2.VideoCapture (in_image_videopath)
    width    = int(inVideo.get (cv.CV_CAP_PROP_FRAME_WIDTH))
    height   = int(inVideo.get (cv.CV_CAP_PROP_FRAME_HEIGHT))
    fps      = int(inVideo.get (cv.CV_CAP_PROP_FPS))
    fourcc   = int(inVideo.get (cv.CV_CAP_PROP_FOURCC))
    logging.info ('frame size: (%dx%d)' % (width,height))
    logging.info ('fps:        %d' % fps)
    logging.info ('codec:      %d' % fourcc)
    if params['write']: 
        outVideo = cv2.VideoWriter(out_mask_videopath, fourcc, fps, (width,height))

    if params['show']: logging.info ('press "space" to pause or "esc" to break and exit')

    counter = 0
    while (True):
        if counter % 1000 == 0: logging.info ('frame %d' % counter) 
        counter += 1

        # read frame and break if the video finished
        gotIt, frame = inVideo.read()
        if not gotIt: break

        # extract and write mask
        mask = fgbg.apply (frame)
        colormask = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
        if params['write']: outVideo.write(colormask)

        # display if necessary
        if params['show']:
            cv2.imshow('display', np.hstack((frame, colormask)))
            button = cv2.waitKey(10)
            if button == 32:
                logging.info ('press any key to continue video')
                cv2.waitKey(-1)
            elif button == 27:
                break

    inVideo.release()
    if params['write']: outVideo.release()
    cv2.destroyAllWindows()



def stackVideos (in_videopath1, in_videopath2, out_videopath):
    ''' 
    Stack frames in two videos together.
    We do NOT check if videos have the same length, dims, etc.
    '''

    inVideo1 = cv2.VideoCapture (in_videopath1)
    inVideo2 = cv2.VideoCapture (in_videopath2)
    width    = int(inVideo1.get (cv.CV_CAP_PROP_FRAME_WIDTH))
    height   = int(inVideo1.get (cv.CV_CAP_PROP_FRAME_HEIGHT))
    fps      = int(inVideo1.get (cv.CV_CAP_PROP_FPS))
    fourcc   = int(inVideo1.get (cv.CV_CAP_PROP_FOURCC))
    logging.info ('frame size: (%dx%d)' % (width,height))
    logging.info ('fps:        %d' % fps)
    logging.info ('codec:      %d' % fourcc)
    outVideo = cv2.VideoWriter(out_videopath, fourcc, fps, (width*2,height))

    while (True):
        gotIt1, frame1 = inVideo1.read()
        gotIt2, frame2 = inVideo2.read()
        if not gotIt1 or not gotIt2: break
        outVideo.write(np.hstack((frame1, frame2)))

    inVideo1.release()
    inVideo2.release()
    outVideo.release()


if __name__ == '__main__':
    logging.basicConfig (level=logging.INFO)

    videopath = op.join (os.getenv('CITY_DATA_PATH'), 'camdata/cam671/Jul28-17h.avi')
    maskpath = op.join (os.getenv('CITY_DATA_PATH'), 'camdata/cam671/Jul28-17h-mask.avi')

    makeMaskVideo (videopath, maskpath, {'show': True, 'write': False})
