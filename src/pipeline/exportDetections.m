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
cameraId = 572;
image = imread([CITY_SRC_PATH 'geometry/cam572.png']);
matFile = [CITY_SRC_PATH 'geometry/' sprintf('Geometry_Camera_%d.mat', cameraId)];
geom = GeometryEstimator(image, matFile);

roadCameraMap = geom.getCameraRoadMap();
orientationMap = geom.getOrientationMap();


% background
background = Background();

% detector
modelPath = [CITY_DATA_PATH, 'violajones/models/model3.xml'];
detector = CascadeCarDetector (modelPath, geom);

% exported detections
outputDir = [CITY_DATA_PATH, 'testdata/learning/detections/'];

for t = 1 : 100
    fprintf('frame %d\n', t);
    
    % read frame
    [frame, timestamp] = frameReader.getNewFrame();
    if isempty(frame), break, end
    gray = rgb2gray(frame);
    
    % write frame as image
    frameName = [sprintf('%03d', t) '-clear.png'];
    imwrite (frame, [outputDir frameName]);

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
        center = cars(i).getCenter();
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
        frame_out = cars(i).drawCar(frame_out, 'color', 'yellow', ...
                                    'tag', num2str(i), 'boxOpacity', 0.1);
        
    end
    % export frame
    frameOutName = [sprintf('%03d', t) '-detections.png'];
    %imwrite (frame_out, [outputDir frameOutName]);
    
end

clear frameReader

