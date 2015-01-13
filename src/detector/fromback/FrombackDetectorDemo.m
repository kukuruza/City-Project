% MultimodelDetectorDemo.m
% Shows how to use the MultimodelDetector class
%

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

run '../../rootPathsSetup.m';
run '../../subdirPathsSetup.m'



%% input

imgPath = '../testdata/5pm-018.png';



%% init

% geometry
objectFile = 'GeometryObject_Camera_572.mat';
load(objectFile);
fprintf ('Have read the Geometry object from file\n');

% load background
% load ([CITY_DATA_PATH 'camdata/cam572/10am/models/backgroundGMM.mat']);
% workaround problem with saving/loading BackgroundDetector - learn now
background = BackgroundGMM('AdaptLearningRate', true, ...
                           'NumTrainingFrames', 50, ...
                           'LearningRate', 0.005, ...
                           'MinimumBackgroundRatio', 0.9, ...
                           'NumGaussians', 2, ...
                           'InitialVariance', 15^2, ...
                           'fn_level', 15, ...
                           'fp_level', 1, ...
                           'minimum_blob_area', 50);
videoDir = [CITY_DATA_PATH 'camdata/cam572/5pm/'];
videoPath = [videoDir '15-mins.avi'];
timesPath = [videoDir '15-mins.txt'];
frameReader = FrameReaderVideo (videoPath, timesPath); 
backimage = imread([videoDir 'models/backimage.png']);
for t = 1 : 100
    [img, ~] = frameReader.getNewFrame();
    img = uint8(int32(img) - int32(backimage) + 128);
    background.subtract(img, 'denoise', false);
end
clear frameReader

% detector
frombackDetector = FrombackDetector(geom, background);



%% work 

% get background in the usual way
img = imread(imgPath);
mask = background.subtract(img, 'denoise', false);

tic
cars = frombackDetector.detect(img, mask);
toc

for i = 1 : length(cars)
    img = cars(i).drawCar(img);
end
imshow([mask2rgb(mask), img]);

