
%run '../rootPathsSetup.m';

global CITY_DATA_PATH;
%global CITY_DATA_LOCAL_PATH;

% patches dir
%imagesDirIn = [CITY_DATA_PATH, 'violajones/KITTI/patches/positive_nequ/0'];
% output features name
%featureFileOut = [CITY_DATA_PATH, 'violajones/cbcl/features/hog-4x3-eq/positive_nequ_KITTI_0.mat'];

% This script extracts features from all the images in a directory
%   and saves them as variable 'features' in a specified file


% % patches dir
% imagesDirIn = [CITY_DATA_PATH, 'violajones/cbcl/patches_negative/'];
% % output features name
% featureFileOut = [CITY_DATA_PATH, 'violajones/cbcl/features/hog-4x3-eq/neg1.mat'];


% get the filenames
% imTemplate = [imagesDirIn, '*.png'];
% imNames = dir (imTemplate);
% 
% featuresCell = cell (length(imNames),1);
% bbs = cell (length(imNames),1);
% names = cell (length(imNames),1);
% 
% for i = 1 : length(imNames)
%     imName = imNames(i);
%     
%     % read
%     img = imread([imagesDirIn, imName.name]);
%     
%     % extract features
%     [imgh, imgw,~]=size(img);
%     bb = [4,4,imgw-4,imgh-4];
%     data(i).imageFilename=[imagesDirIn, imName.name];
%     data(i).objectBoundingBoxes=bb;
%     % save
% 
% end

%save 'data' [names,bbs);

% write resulting feature to a variable
%save(featureFileOut, 'features');

%data=positiveInstances;
load 'data.mat'
imDir = '/Users/lgui/Documents/MATLAB/data/cameraNumber360';
addpath(imDir);

%negativeFolder = fullfile(matlabroot, 'toolbox', 'vision','visiondemos', 'non_stop_signs');
negativeFolder = '/Users/lgui/Documents/MATLAB/data/negativeTest';
negativeFolder = fullfile(matlabroot, 'toolbox', 'vision','visiondemos', 'non_stop_signs');
%negativeFolder = '/Users/lgui/Documents/MATLAB/data/background';

% strcmp(imagename, '/Users/lgui/Documents/MATLAB/data/cam360/car_0558.ppm')
trainCascadeObjectDetector('carDetector.xml', data, negativeFolder, 'FalseAlarmRate', 0.9, 'NumCascadeStages', 5);

detector = vision.CascadeObjectDetector('carDetector.xml');

img = imread('/Users/lgui/Box Sync/City Project/data/five camera for 2 min/cameraNumber360/image0002.jpg');

bbox = step(detector, img);

detectedImg = insertObjectAnnotation(img, 'rectangle', bbox, 'car');

figure; imshow(detectedImg);