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

%imPath = '../testdata/10am-064.jpg';
imPath = '../testdata/5pm-018.png';


%% init

% geometry
objectFile = 'GeometryObject_Camera_572.mat';
load(objectFile);
fprintf ('Have read the Geometry object from file\n');

% background - load parameters and learn
% workaround problem with saving/loading BackgroundDetector - learn now
load ([CITY_DATA_PATH 'camdata/cam572/10am/models/backgroundGMM.mat']);
videoDir = [CITY_DATA_PATH 'camdata/cam572/5pm/'];
videoPath = [videoDir '15-mins.avi'];
timesPath = [videoDir '15-mins.txt'];
frameReader = FrameReaderVideo (videoPath, timesPath); 
backimage = imread([videoDir 'models/backimage.png']);
for t = 1 : 100
    [img, ~] = frameReader.getNewFrame();
    img = uint8(int32(img) - int32(backimage) + 128);
    background.subtract(img, 'denoise', false);
end
clear frameReader

% from-background detector
cluster_fromback = struct('minyaw', -180, 'maxyaw', 180, 'minsize', 20, 'maxsize', 500, 'carsize', [20 15]);
cluster_fromback.recallMask = logical(ones(size(img,1), size(img,2)));
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
multiDetector = MultimodelDetector(usedClusters, detectors);

img0 = imread(imPath);
img = img0;

% necessary for FrombackDetector
background.subtract(img, 'denoise', false);

tic
cars = multiDetector.detect(img);
toc

for i = 1 : length(cars)
    img = cars(i).drawCar(img);
end

img = img + uint8(multiDetector.getMask('colormask', true) * 20);
imshow([img0, img; mask2rgb(background.result), uint8(abs(img0 - 255))]);

