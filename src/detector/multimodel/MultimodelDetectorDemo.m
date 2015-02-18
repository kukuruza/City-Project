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

modelTemplate = 'violajones/models/model%02d-cr10.xml';

imSrcPath = '../testdata/081-clear.png';
backimagePath = '../testdata/backimage.png';
%imSrcPath = '../testdata/5pm-018-src.png';

imSrc = imread (imSrcPath);
backimage = imread (backimagePath);
img0 = uint8( int32(imSrc) - int32(backimage) + 128 );

%% init

% geometry
load([CITY_DATA_PATH, 'models/cam572/GeometryObject_Camera_572.mat']);
fprintf ('Have read the Geometry object from file\n');

% background - load parameters and learn
% workaround problem with saving/loading BackgroundDetector - learn now
load ([CITY_DATA_PATH 'models/cam572/backgroundGMM.mat']);
pretrainBackground (background, [CITY_DATA_PATH 'camdata/cam572/5pm/']);

% from-background detector
cluster_fromback = struct('minyaw', -180, 'maxyaw', 180, 'minsize', 20, 'maxsize', 500, 'carsize', [20 15]);
sz = size(geom.getCameraRoadMap());
cluster_fromback.recallMask = true(sz);
cluster_fromback.name = 'foregr.';
frombackDetector = FrombackDetector(geom, background);
frombackDetector.mask = cluster_fromback.recallMask;


% arrays of viola-jones clusters and detectors
counter = 1;
for i = iclusters
    usedClusters(counter) = clusters(i);
    
    modelPath = sprintf(modelTemplate, i);
    detectors{counter} = CascadeCarDetector(modelPath, geom, ...
        'minsize', clusters(i).carsize);
    detectors{counter}.mask = clusters(i).recallMask;

    counter = counter + 1;
end

% add fromback_detector
usedClusters(counter) = cluster_fromback;
detectors{counter} = frombackDetector;

% multimodel detector
multiDetector = MultimodelDetector(usedClusters, detectors, 'verbose', 3);
multiDetector.noMerge = true;


% save multiDetector under name 'detector'
detector = multiDetector; 
save ([CITY_DATA_PATH 'models/cam572/multiDetector.mat'], 'detector');
clear detector;

img = img0;

% necessary for FrombackDetector
background.subtract(img, 'denoise', false);

tic
cars = multiDetector.detect(img);
toc

cmap = colormap('Autumn');
for i = 1 : length(cars)
    colorindex = floor(cars(i).score * size(cmap,1)) + 1;
    color = cmap (colorindex, :) * 255;
    img = cars(i).drawCar(img, 'boxOpacity', 0.0, 'FontSize', 20, 'color', color );
end
img = img + uint8(multiDetector.getMask('colormask', true) * 30);
%imshow([img0, img; mask2rgb(background.result), gray2darkghost(img0)]);
imshow(img);
error('stop here');
pause

for i = 1 : length(cars)
    img = imSrc;
    img = cars(i).drawCar( img, 'boxOpacity', 0.0, 'FontSize', 20);
    imshow(img);
    pause
end

