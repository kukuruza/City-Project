% MultimodelDetectorDemo.m
% Shows how to use the MultimodelDetector class
%

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

run '../../rootPathsSetup.m';
run '../../subdirPathsSetup.m'



%% input

iclusters = [1 2 3 4];

clustersPath = [CITY_DATA_PATH 'violajones/patches/clusters.mat'];
load (clustersPath);

modelTemplate = [CITY_DATA_PATH, 'violajones/models/model%02d-cr10.xml'];

imPath = '../testdata/10am-064.jpg';
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
    detectors(counter) = CascadeCarDetector(modelPath, geom, ...
        'minsize', clusters(i).carsize);
    
    counter = counter + 1;
end

% multimodel detector
multiDetector = MultimodelDetector(usedClusters, detectors);

tic
cars = multiDetector.detect(img0);
toc

img = img0;
for i = 1 : length(cars)
    img = cars(i).drawCar(img);
end

img = img + uint8(multiDetector.getMask('colormask', true) * 20);
imshow(img);

