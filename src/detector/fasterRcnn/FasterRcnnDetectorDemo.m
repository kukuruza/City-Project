clear all

%% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script



%% input
model_dir = fullfile(getenv('FASTERRCNN_ROOT'), 'output/faster_rcnn_final/faster_rcnn_VOC0712_ZF');
image_path  = '../testdata/image00001.png';


%% init

% detector
fasterRcnnDetector = FasterRcnnDetector (model_dir, 'use_gpu', true);

%% work 

img =  imread(image_path);

tic
%fasterRcnnDetector.setVerbose(1);
cars = fasterRcnnDetector.detect(img);
toc

cmap = colormap('Autumn');
for i = 1 : length(cars)
    colorindex = floor(cars(i).score * size(cmap,1)) + 1;
    color = cmap (colorindex, :) * 255;
    img = cars(i).drawCar(img, 'color', color);
end
imwrite(img, 'resultdemo.jpg');
%imshow([mask2rgb(mask), img]);

