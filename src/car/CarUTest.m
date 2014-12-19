% test for Car - test class methods
%

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% setup all the paths
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m;

% geometry
objectFile = 'GeometryObject_Camera_572.mat';
load(objectFile);
fprintf ('Have read the Geometry object from file\n');
roadCameraMap = geom.getCameraRoadMap();

% input cars
inCarsDir = [CITY_DATA_PATH 'testdata/detector/detections/'];

image = imread([CITY_DATA_PATH 'testdata/car/002.png']);
carsList = dir([inCarsDir '002-car*.mat']);

for i = 1 : length(carsList)
    % load car object
    clear car
    load ([inCarsDir carsList(i).name]);

    % extract and show patch
    patch = car.extractPatch (image);
    figure(1)
    imshow(patch);

    % refine patch
    patch = car.extractPatch (image, 'segment','maxflow');
    figure(2)
    imshow(patch);
    figure(3)
    imshow(car.segmentMask);

    pause
end


