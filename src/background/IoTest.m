clear all

detector = vision.ForegroundDetector();
image = imread ('testdata/ioTest-fr0.png');
mask = step(detector, image);

image = imread ('testdata/ioTest-fr1.png');
mask = step(detector, image);

feature('SystemObjectsFullSaveLoad',1);
save('testdata/ioTest-detector.mat', 'detector');

clear all
load('testdata/ioTest-detector.mat');

image = imread ('testdata/ioTest-fr0.png');
mask = step(detector, image);
