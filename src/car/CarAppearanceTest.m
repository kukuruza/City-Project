% test for extracting features
%

% input constants
image = imread('testdata/cam493_im0068.jpg');
bbox = [150 160 100 75];
iFrame = 1;

% create car
car = CarAppearance(bbox, iFrame);

% test patch extraction
imshow (car.extractPatch(image));

% test generated feature
car.generateFeature(image);
car.feature
