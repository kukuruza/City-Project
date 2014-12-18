% test for mask2roi
%

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% setup all the paths
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m;

% input mask
inCarsDir = [CITY_DATA_PATH 'testdata/utilities/mask2roi/'];
mask = imread([inCarsDir 'mask.png']);

roi = mask2roi(mask);
bbox = [roi(2), roi(1), roi(4)-roi(2)+1, roi(3)-roi(1)+1];

mask = insertObjectAnnotation (uint8(mask*255), 'rectangle', bbox, 'label');
imshow(mask);
