%% merging detection bbx
clear all;
close all;
clc

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script

carsDir = 'testdata/';
frameName = '008';

% function from 'utilities' to load all car objects
cars = loadCars(carsDir, 'nameTemplate', [frameName '*.mat']);

% show original detections
img = imread([carsDir sprintf('%s-clear.png', frameName)]);
imgOrig = drawCars(img, cars);

% show filtered detections
mergedCars = mergeCars (cars, 'overlap', .8);
imgMerged =  drawCars(img, mergedCars);

imshow ([imgOrig imgMerged]);
