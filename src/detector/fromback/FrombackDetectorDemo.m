clear all

%% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script



%% input
image_path  = '../testdata/image00001.png';
mask_path   = '../testdata/mask00001.png';

mapSize_path = 'models/cam572/mapSize.tiff';


%% init

% size map
size_map = imread(fullfile(CITY_DATA_PATH, mapSize_path));

% detector
frombackDetector = FrombackDetector(size_map);
%frombackDetector.noFilter = true;


%% work 

img =  imread(image_path);
mask = imread(mask_path);
mask = mask(:,:,1) > 127;

tic
cars = frombackDetector.detect(img, mask);
toc

cmap = colormap('Autumn');
for i = 1 : length(cars)
    colorindex = floor(cars(i).score * size(cmap,1)) + 1;
    color = cmap (colorindex, :) * 255;
    img = cars(i).drawCar(img, 'color', color);
end
imshow([mask2rgb(mask), img]);

