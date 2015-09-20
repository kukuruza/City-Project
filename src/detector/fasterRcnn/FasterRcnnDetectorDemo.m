clear all

%% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script



%% input
image_path  = '../testdata/image00001.png';


%% init

% detector
fasterRcnnDetector = FasterRcnnDetector ('use_gpu', false);


%% work 

img =  imread(image_path);

tic
cars = fasterRcnnDetector.detect(img, mask);
toc

cmap = colormap('Autumn');
for i = 1 : length(cars)
    colorindex = floor(cars(i).score * size(cmap,1)) + 1;
    color = cmap (colorindex, :) * 255;
    img = cars(i).drawCar(img, 'color', color);
end
imwrite(img, 'resultdemo.jpg');
%imshow([mask2rgb(mask), img]);

