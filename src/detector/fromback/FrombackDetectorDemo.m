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
load([CITY_DATA_PATH, 'models/cam572/GeometryObject_Camera_572.mat']);
fprintf ('Have read the Geometry object from file\n');

% load background
load ([CITY_DATA_PATH 'models/cam572/backgroundGMM.mat']);
pretrainBackground (background, [CITY_DATA_PATH 'camdata/cam572/5pm/']);

% detector
frombackDetector = FrombackDetector(geom, background);
%frombackDetector.noFilter = true;


%% work 

% get background in the usual way
img = imread(imgPath);
mask = background.subtract(img, 'denoise', false);

tic
cars = frombackDetector.detect(img);
toc

cmap = colormap('Autumn');
for i = 1 : length(cars)
    colorindex = floor(cars(i).score * size(cmap,1)) + 1;
    color = cmap (colorindex, :) * 255;
    img = cars(i).drawCar(img, 'color', color);
end
imshow([mask2rgb(mask), img]);

