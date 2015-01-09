% MultimodelDetectorDemo.m
% Shows how to use the MultimodelDetector class
%

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

run '../../rootPathsSetup.m';
run '../../subdirPathsSetup.m'



%% input

iclusters = [1 3];

clustersPath = [CITY_DATA_PATH 'violajones/patches/clusters.mat'];
load (clustersPath);

modelTemplate = [CITY_DATA_PATH, 'violajones/models/model%02d-cr10.xml'];

imPath = [CITY_DATA_PATH, 'testdata/detector/064-ghosts.jpg'];
img0 = imread(imPath);



%% init

% geometry
objectFile = 'GeometryObject_Camera_572.mat';
load(objectFile);
fprintf ('Have read the Geometry object from file\n');

% arrays of clusters and detectors
counter = 1;
for i = iclusters
    usedClusters(counter) = clusters(i);
    
    modelPath = sprintf(modelTemplate, i);
    detectors(counter) = CascadeCarDetector(modelPath, geom);
    
    counter = counter + 1;
end

% multimodel detector
multiDetector = MultimodelDetector(usedClusters, detectors);

tic
cars = multiDetector.detect(img0);
toc

img = img0;
for i = 1 : length(cars)
    img = insertObjectAnnotation(img, 'rectangle', cars(i).bbox, 'car');
end
figure (1);
imshow(img);



