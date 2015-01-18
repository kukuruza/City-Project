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
load ([CITY_DATA_PATH 'models/cam572/backgroundGMM.mat']);
pretrainBackground (background, [CITY_DATA_PATH 'camdata/cam572/5pm/']);

% detector
frombackDetector = FrombackDetector(geom, background);
frombackDetector.noFilter = true;


%% work 

% get background in the usual way
img = imread(imgPath);
mask = background.subtract(img, 'denoise', false);

tic
cars = frombackDetector.detect(img);
toc

for i = 1 : length(cars)
    img = cars(i).drawCar(img);
end
imshow([mask2rgb(mask), img]);

