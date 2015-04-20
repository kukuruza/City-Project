import numpy as np
import cv2
import sys, os, os.path as op
#sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))


video_path = op.join(os.getenv('CITY_DATA_PATH'), 'camdata/cam717/Apr09-09h.avi')

cap = cv2.VideoCapture(video_path)

fgbg = cv2.BackgroundSubtractorMOG()

while(1):
    ret, frame = cap.read()

    fgmask = fgbg.apply(frame)

    cv2.imshow('frame',fgmask)
    k = cv2.waitKey(30) & 0xff
    if k == 27:
        break

cap.release()
cv2.destroyAllWindows()