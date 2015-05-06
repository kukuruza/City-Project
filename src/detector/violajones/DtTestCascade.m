% detect object using trained cascade classifier

clear all

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script


% test images dir
%imagesDir = [CITY_DATA_PATH, 'violajones/testdata/images/'];
modelPath = [CITY_DATA_PATH, 'violajones/models/model01-cr10.xml'];

% load model
detector = vision.CascadeObjectDetector(modelPath);

% detect

imPath = 'testdata/smallCars.png';
%imPath = [CITY_DATA_PATH 'learning/cam572-sparse/frames/1153-ghosts.jpg'];
img = imread(imPath);

% % threshold noise
% imggray = rgb2gray(img);
% noisemask = abs(imggray - 128) < 1;
% noisemask = reshape(noisemask, size(imggray));
% imshow(noisemask);
% img(noisemask) = 128;
% img(noisemask + numel(noisemask) * 1) = 128;
% img(noisemask + numel(noisemask) * 2) = 128;

bboxes = step(detector, img);
detectedImg = insertObjectAnnotation(img, 'rectangle', bboxes, 'car');
figure; imshow(detectedImg);
