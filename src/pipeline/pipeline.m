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
frameReader = FrameReaderImages ([CITY_DATA_PATH '2-min/camera572/']); 
im0 = frameReader.getNewFrame();

% geometry
objectFile = 'GeometryObject_Camera_572.mat';
load(objectFile);
fprintf ('Have read the Geometry object from file\n');
roadCameraMap = geom.roadCameraMap(im0);

% background
subtractor = BackgroundSubtractor(5, 25, 80);

% detector
modelPath = [CITY_DATA_PATH, 'violajones/models/model3.xml'];
detector = CascadeCarDetector (modelPath);
frameid = 0;

% 
counting = MetricLearner(); % pass necessary arguments to constructor
countcars = 0;


t = 1;
while 1
    tic
    
    % read image
    [frame, interval] = frameReader.getNewFrame();
    frameid = frameid + interval;
    if isempty(frame), break, end
    gray = rgb2gray(frame);
    
    % subtract backgroubd and return mask
    % bboxes = N x [x1 y1 width height]
    foregroundMask = subtractor.subtractAndDenoise(gray);

    % geometry processing mask and bboxes
    foregroundMask = foregroundMask & logical(roadMask);
    
    % actually detect cars
    tic
    cars = detector.detect(frame);%, scales(j), orientations(j));
    toc
    
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
        fprintf('expectedSize: %f ', expectedSize);
        fprintf('actualSize: %f\n', cars(k).bbox(3));
        if expectedSize / SizeTolerance < cars(k).bbox(3) && ...
           expectedSize * SizeTolerance > cars(k).bbox(3)
            carsFilt(counter) = cars(k);
            counter = counter + 1;
        end
    end
    cars = carsFilt;    
    
    % count cars
    for i = 1:length(cars)
         cars(i).iFrame = t;
         cars(i).extractPatch(frame);
    end
    [newCarNumber, ~] = counting.processFrame(t, frame, cars, geom);
    countcars = countcars + newCarNumber;
    
    % output
    tCycle = toc;
    frame_out = frame;
    for j = 1 : length(cars)
        frame_out = cars(j).drawCar(frame_out);
    end
    imshow(frame_out);
    
    t = t + 1;
    fprintf ('frame %d in %f sec \n', t, tCycle);
end
