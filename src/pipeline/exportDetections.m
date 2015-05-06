% test pipeline
%
% This file reads images from a directory and processes them one by one,
%   as if they were coming real-time.
%

clear all

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script

% input frames
videoDir = [CITY_DATA_PATH 'camdata/cam572/5pm/'];
videoPath = [videoDir '15-mins.avi'];
timesPath = [videoDir '15-mins.txt'];
frameReader = FrameReaderVideo (videoPath, timesPath); 

% geometry
load([CITY_DATA_PATH, 'models/cam572/GeometryObject_Camera_572.mat']);
roadCameraMap = geom.getCameraRoadMap();
orientationMap = geom.getOrientationMap();

% background
load ([CITY_DATA_PATH 'models/cam572/backgroundGMM.mat']);
pretrainBackground (background, [CITY_DATA_PATH 'camdata/cam572/5pm/']);
backimage = imread([videoDir 'models/backimage.png']);

% detector
load ([CITY_DATA_PATH 'models/cam572/multiDetector.mat']);
detector.noMerge = false;
detector.setVerbosity(0);
detector.detectors{5}.background = background;

% exported detections
outputDir = [CITY_DATA_PATH, 'testdata/detector/detections/'];

for t = 1 : 100
    fprintf('frame %d\n', t);
    
    % read frame
    [frame, timestamp] = frameReader.getNewFrame();
    if isempty(frame), break, end
    frame_ghost = uint8(int32(frame) - int32(backimage) + 128);
    
    % write frame as image
    frameName = [sprintf('%03d', t) '-clear.png'];
    imwrite (frame, [outputDir frameName]);

    % subtract backgroubd and return mask
    % bboxes = N x [x1 y1 width height]
    foregroundMask = background.subtract(frame_ghost, 'denoise', true);

    % geometry processing mask and bboxes
    foregroundMask = foregroundMask & logical(roadCameraMap);
    
    % actually detect cars
    cars = detector.detect(frame_ghost);
    
    % assign timestamps to cars
    for i = 1 : length(cars)
        cars(i).timeStamp = timestamp;
        center = cars(i).getBottomCenter();
        cars(i).orientation = [orientationMap.yaw(center(1), center(2)), ...
                               orientationMap.pitch(center(1), center(2))];
    end
    
    % filter detected cars based on foreground mask
    counter = 1;
    carsFilt = Car.empty;
    for i = 1 : length(cars)
        center = cars(i).getCenter(); % [y x]
        if foregroundMask(center(1), center(2))
            carsFilt(counter) = cars(i);
            counter = counter + 1;
        end
    end
    cars = carsFilt;
    
    % filtering cars based on sizes
    SizeTolerance = 1.5;
    counter = 1;
    carsFilt = Car.empty;
    for i = 1 : length(cars)
        center = cars(i).getCenter(); % [y x]
        expectedSize = roadCameraMap(center(1), center(2));
        if expectedSize / SizeTolerance < cars(i).bbox(3) && ...
           expectedSize * SizeTolerance > cars(i).bbox(3)
            carsFilt(counter) = cars(i);
            counter = counter + 1;
        end
    end
    cars = carsFilt;
    fprintf ('pipeline: left good detections: %d\n', length(cars));
    
    % output
    frame_out = frame;
    for i = 1 : length(cars)
        
        % export car
        car = cars(i);
        car.patch = car.extractPatch(frame);
        namePrefix = [sprintf('%03d', t) '-car' sprintf('%03d', i)];
        save ([outputDir namePrefix '.mat'], 'car');
        %imwrite (car.patch, [outputDir namePrefix '.png']);
        
        % draw patch on image
        cmap = colormap('Autumn');
        colorindex = floor(cars(i).score * size(cmap,1)) + 1;
        color = cmap (colorindex, :) * 255;
        frame_out = cars(i).drawCar(frame_out, 'color', color, ...
                                    'tag', num2str(i), 'boxOpacity', 0.1);
        
    end
    % export frame
    frameOutName = [sprintf('%03d', t) '-detections.png'];
    imwrite (frame_out, [outputDir frameOutName]);
    
end

clear frameReader

