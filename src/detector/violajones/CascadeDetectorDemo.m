% detect object using trained cascade classifier

clear all

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script



%% input

%imPath = '../testdata/10am-064.jpg';
imPath = '../testdata/5pm-018.png';
img = imread(imPath);
%thresh = 2;
%mask = abs(img(:,:,1) - 128) < thresh & ...
%       abs(img(:,:,2) - 128) < thresh & ...
%       abs(img(:,:,3) - 128) < thresh;
%img(mask(:,:,[1 1 1])) = 128;

verbose = 0;


%% detect and refine

modelPath = 'learning/violajones/models/May17-high-yaw/ex0.1-noise1.5-pxl5/cascade.xml';
minsize = [18 24];

detector = CascadeCarDetector(modelPath, 'minsize', minsize, 'cropPercent', 0.1);

tic
cars = detector.detect(img);
toc

cmap = colormap('Autumn');
for i = 1 : length(cars)
    colorindex = floor(cars(i).score * (size(cmap,1)-1)) + 1;
    color = cmap (colorindex, :) * 255;
    img = cars(i).drawCar(img, 'color', color);
end

% show detector's mask
if verbose
    bbox = roi2bbox(mask2roi(detector.mask > 0));
    img = insertObjectAnnotation(img, 'rectangle', bbox, 'sizeMap bbox', 'Color', 'blue');
    mask = detector.mask > 0;
    img = img + 50 * uint8(mask(:,:,[1 1 1]));
end

figure(1)
imshow(img);





