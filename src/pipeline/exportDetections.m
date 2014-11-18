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
videoPath = [CITY_DATA_PATH 'camdata/cam572/5pm/15-mins.avi'];
timesPath = [CITY_DATA_PATH 'camdata/cam572/5pm/15-mins.txt'];
frameReader = FrameReaderVideo (videoPath, timesPath); 

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

% exported detections
outputDir = [CITY_DATA_PATH, 'testdata/carcount/detections/'];

for t = 1 : 100
    fprintf('frame %d\n', t);
    
    % read frame
    [frame, timestamp] = frameReader.getNewFrame();
    if isempty(frame), break, end
    gray = rgb2gray(frame);
    
    % subtract backgroubd and return mask
    % bboxes = N x [x1 y1 width height]
    foregroundMask = background.subtractAndDenoise(gray);

    % geometry processing mask and bboxes
    foregroundMask = foregroundMask & logical(roadCameraMap);
    
    % actually detect cars
    cars = detector.detect(frame);
    
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
        frame_out = cars(i).drawCar(frame_out, 'yellow', num2str(i), 0.1);
        
    end
    % export frame
    frameName = [sprintf('%03d', t) '.png'];
    imwrite (frame_out, [outputDir frameName]);
    
end

clear frameReader

