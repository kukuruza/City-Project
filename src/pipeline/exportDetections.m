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
    
    % output
    frame_out = frame;
    for j = 1 : length(cars)
        
        % export patch
        patch = cars(j).extractPatch(frame);
        patchName = [sprintf('%03d', t) '-patch' sprintf('%03d', j) '.png'];
        imwrite (patch, [outputDir patchName]);
        
        % draw patch on image
        frame_out = cars(j).drawCar(frame_out, 'yellow', num2str(j));
        
    end
    % export frame
    frameName = [sprintf('%03d', t) '.png'];
    imwrite (frame_out, [outputDir frameName]);
    
end

clear frameReader

