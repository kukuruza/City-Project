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

camNum = 572;

% input frames
videoPath = [CITY_DATA_PATH 'camdata/cam572/5pm/15-mins.avi'];
timesPath = [CITY_DATA_PATH 'camdata/cam572/5pm/15-mins.txt'];
frameReader = FrameReaderVideo (videoPath, timesPath); 
im0 = frameReader.getNewFrame();

% geometry
objectFile = 'GeometryObject_Camera_572.mat';
load(objectFile);
fprintf ('Have read the Geometry object from file\n');
roadCameraMap = geom.getCameraRoadMap();

% background
background = Background();

% detector
modelPath = [CITY_DATA_PATH, 'violajones/models/model3.xml'];
detector = CascadeCarDetector (modelPath);
frameid = 0;

% probabilistic model
counting = MetricLearner(geom);
countcars = 0;

% output results
outputPath = [CITY_DATA_PATH, 'testdata/pipeline/cam572-5pm.avi'];
frameWriter = FrameWriterVideo (outputPath, 2, 1);

t = 1;
while 1
    tic
    
    if t == 100, break, end
    
    % read image
    [frame, interval] = frameReader.getNewFrame();
    frameid = frameid + interval;
    if isempty(frame), break, end
    gray = rgb2gray(frame);
    
    % subtract backgroubd and return mask
    % bboxes = N x [x1 y1 width height]
    foregroundMask = background.subtractAndDenoise(gray);

    % geometry processing mask and bboxes
    foregroundMask = foregroundMask & logical(roadCameraMap);
    
    % actually detect cars
    cars = detector.detect(frame); % orientations(j));
    
    % filter detected cars based on foreground mask
    counter = 1;
    carsFilt = Car.empty;
    for k = 1 : length(cars)
        center = cars(k).getCenter(); % [y x]
        if foregroundMask(center(1), center(2))
            carsFilt(counter) = cars(k);
            counter = counter + 1;
        end
    end
    cars = carsFilt;
    
    % filtering cars based on sizes
    SizeTolerance = 1.5;
    counter = 1;
    carsFilt = Car.empty;
    for k = 1 : length(cars)
        center = cars(k).getCenter(); % [y x]
        expectedSize = roadCameraMap(center(1), center(2));
        if expectedSize / SizeTolerance < cars(k).bbox(3) && ...
           expectedSize * SizeTolerance > cars(k).bbox(3)
            carsFilt(counter) = cars(k);
            counter = counter + 1;
        end
    end
    cars = carsFilt;
    fprintf ('pipeline: filtered detections: %d\n', length(cars));
    
    % count cars
    [newCarNumber, ~, newCarIndices] = counting.processFrame(frame, cars);
    fprintf ('pipeline: new cars: %d\n', newCarNumber);
    countcars = countcars + newCarNumber;
    
    % Drawing the current frame for visualzing the speed change
    nextPosImage = geom.drawNextPosition(cars, frame);
    figure(2); imshow(nextPosImage)
    
    % output
    frame_out = frame;
    for j = 1 : length(cars)
        if newCarIndices(j) == 0, tagColor = 'blue';
        else tagColor = 'yellow'; 
        end
        frame_out = cars(j).drawCar(frame_out, tagColor);
    end
    figure(1); imshow(frame_out);
    frameWriter.writeNextFrame(frame_out);
    
    tCycle = toc;
    t = t + 1;
    fprintf ('frame %d in %f sec \n \n', t, tCycle);
end

clear frameWriter frameReader

