%% merging detection bbx
clear all;
close all;
clc

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% change ../.. to the relative path of the file
run '../../rootPathsSetup.m';
run '../../subdirPathsSetup.m';

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
