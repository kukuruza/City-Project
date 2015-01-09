% detect object using trained cascade classifier

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% add all scripts to matlab pathdef
run ../../rootPathsSetup.m;
run ../../subdirPathsSetup.m;


% test images dir
%imagesDir = [CITY_DATA_PATH, 'violajones/testdata/images/'];
modelPath = [CITY_DATA_PATH, 'violajones/models/model-03-cr10.xml'];

% load model
detector = vision.CascadeObjectDetector(modelPath);

% detect
imPath = [CITY_DATA_PATH 'learning/cam572-sparse/frames/1153-ghosts.jpg'];
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
