% test pipeline
%
% This file reads images from a directory and processes them one by one,
%   as if they were coming real-time.
%

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% setup all the paths
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m;

% input frames
videoDir = [CITY_DATA_PATH 'camdata/cam572/5pm/'];
videoPath = [videoDir '15-mins.avi'];
timesPath = [videoDir '15-mins.txt'];
frameReader = FrameReaderVideo (videoPath, timesPath); 

% geometry
objectFile = 'GeometryObject_Camera_572.mat';
load(objectFile);
fprintf ('Have read the Geometry object from file\n');
roadCameraMap = geom.getCameraRoadMap();

% background
load ([CITY_DATA_PATH 'models/cam572/backgroundGMM.mat']);
pretrainBackground (background, [CITY_DATA_PATH 'camdata/cam572/5pm/']);
backimage = imread([videoDir 'models/backimage.png']);

% detector
load ([CITY_DATA_PATH 'models/cam572/multiDetector.mat']);

detector.detectors{5}.background = background;

% probabilistic model
counting = MetricLearner(geom);
countcars = 0;

% output results
outputPath = [CITY_DATA_PATH, 'testdata/pipeline/cam572-5pm.avi'];
frameWriter = FrameWriterVideo (outputPath, 2, 1);

% cache seen cars from previous frame
seenCars = [];

for t = 1 : 100
    fprintf('frame %d\n', t);
    tic
    
    % read image
    [frame, timestamp] = frameReader.getNewFrame();
    if isempty(frame), break, end
    frame_ghost = uint8(int32(frame) - int32(backimage) + 128);
    
    % subtract backgroubd and return mask
    % bboxes = N x [x1 y1 width height]
    foregroundMask = background.subtract(frame_ghost, 'denoise', true);

    % geometry processing mask and bboxes
    %foregroundMask = foregroundMask & logical(roadCameraMap);
    
    % actually detect cars
    cars = detector.detect(frame_ghost);
    
    % assign timestamps to cars
    for i = 1 : length(cars)
        cars(i).timeStamp = timestamp;
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
    fprintf ('pipeline: filtered detections: %d\n', length(cars));
    
    % count cars
    [newCarNumber, transitionMatrix, newCarIndices] = counting.processFrame(frame, cars);
    fprintf ('pipeline: new cars: %d\n', newCarNumber);
    countcars = countcars + newCarNumber;
    
    % Drawing the current frame for visualzing the speed change
    %nextPosImage = geom.drawNextPosition(cars, frame);
    %figure(2); imshow(nextPosImage)
    
    % output
    frame_out = frame;
    for i = 1 : length(cars)
        if newCarIndices(i) == 0
            frame_out = cars(i).drawCar(frame_out, 'color', 'blue', 'tag', 'seen');
        else 
            frame_out = cars(i).drawCar(frame_out, 'color', 'yellow', 'tag', 'new');
        end
    end
    
    frame_out = drawCarTransitions(seenCars, cars, transitionMatrix, frame_out);
    imshow([frame_ghost ... % gray2darkghost(frame_ghost) ...
            frame_out]);
    %frameWriter.writeNextFrame(frame_out);
    
    seenCars = cars;
    tCycle = toc;
    fprintf ('frame %d in %f sec \n \n', t, tCycle);
    
    pause
end

clear frameWriter frameReader

