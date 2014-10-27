% detect object using trained cascade classifier

%clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

run '../../rootPathsSetup.m';
run '../../subdirPathsSetup.m'

% test images dir
imagesDir = [CITY_DATA_PATH, 'testdata/detector/'];
modelPath = [CITY_DATA_PATH, 'violajones/models/model3.xml'];

avgsize = [18 36];
detector = CascadeCarDetector(modelPath, avgsize);

% detect
imPath = [imagesDir '000000.jpg'];
img = imread(imPath);
%roi = [100 50 250 310];   % [y1 x1 y2 x2];
%img = img(roi(1) : roi(3), roi(2) : roi(4));
%img = imresize(img, 1.8);

tic
cars = detector.detect(img);
toc
for i = 1 : length(cars)
    img = insertObjectAnnotation(img, 'rectangle', cars(i).bbox, 'car');
end
imshow(img);
