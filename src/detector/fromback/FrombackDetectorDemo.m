% MultimodelDetectorDemo.m
% Shows how to use the MultimodelDetector class
%

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

run '../../rootPathsSetup.m';
run '../../subdirPathsSetup.m'



%% input

imPath = '../testdata/5pm-018.png';
img = imread(imPath);



%% init

% geometry
objectFile = 'GeometryObject_Camera_572.mat';
load(objectFile);
fprintf ('Have read the Geometry object from file\n');

% load background
load ([CITY_DATA_PATH 'camdata/cam572/5pm/models/backgroundGMM.mat']);

% detector
frombackDetector = FrombackDetector(geom, background);



%% work 

% get background in the usual way
mask = background.subtract(img, 'denoise', true);

tic
cars = frombackDetector.detect(img, mask);
toc

for i = 1 : length(cars)
    img = cars(i).drawCar(img);
end
imshow(img);

