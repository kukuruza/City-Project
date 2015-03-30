#import library - MUST use cv2 if using opencv_traincascade
import cv2
import sys
import os, os.path as op

CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')

# rectangle color and stroke
color = (0,0,255)       # reverse of RGB (B,G,R) - weird
strokeWeight = 1        # thickness of outline

# set window name
windowName = "Object Detection"

# load an image to search for faces
#img = cv2.imread("/Users/evg/projects/City-Project/data/testdata/detector/img000.jpg");
img = cv2.imread(op.join(CITY_DATA_PATH, 'datasets/labelme/Ghosts/cam572-bright-frames/000015.jpg'))
print (img.shape)

# load detection file (various files for different views and uses)
model_path = op.join(CITY_DATA_PATH, 'learning/violajones/cars_24x18-e0.3/model-masked/cascade.xml')
#model_path = op.join(CITY_DATA_PATH, 'learning/violajones/models/model03-cr10.xml')
if not op.exists(model_path):
    raise Exception ('mode_path does not exist: ' + model_path)
cascade = cv2.CascadeClassifier (model_path)

# preprocessing, as suggested by: http://www.bytefish.de/wiki/opencv/object_detection
# img_copy = cv2.resize(img, (img.shape[1]/2, img.shape[0]/2))
# gray = cv2.cvtColor(img_copy, cv2.COLOR_BGR2GRAY)
# gray = cv2.equalizeHist(gray)

b,g,r = cv2.split(img)
ret,thresh1 = cv2.threshold(img,127,255,cv2.THRESH_BINARY)

# detect objects, return as list
rects = cascade.detectMultiScale(img)
print ('detected ' + str(len(rects)))
if rects is None or len(rects) == 0: sys.exit()

# display until escape key is hit
while True:

    # get a list of rectangles
    for x,y, width,height in rects:
        cv2.rectangle(img, (x,y), (x+width, y+height), color, strokeWeight)

    # display!
    cv2.imshow(windowName, img)

    # escape key (ASCII 27) closes window
    if cv2.waitKey(20) == 27:
        break

# if esc key is hit, quit!
exit()