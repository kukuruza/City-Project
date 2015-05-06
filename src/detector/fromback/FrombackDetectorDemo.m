% MultimodelDetectorDemo.m
% Shows how to use the MultimodelDetector class
%

clear all

%% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script



%% input
video_file  = 'camdata/cam572/Oct30-17h.avi';
back_file   = 'camdata/cam572/Oct30-17h-back.png';

imgPath = '../testdata/5pm-018.png';


%% init

% geometry
load([CITY_DATA_PATH, 'models/cam572/GeometryObject_Camera_572.mat']);

% background
background = BackgroundGMM('pretrain_video_path', [CITY_DATA_PATH video_file], ...
                           'pretrain_back_path', [CITY_DATA_PATH back_file]);

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

