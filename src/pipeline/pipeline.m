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
%matFile = [CITY_SRC_PATH 'geometry/Geometry_Camera_572.mat'];
%geom = GeometryEstimator(im0, matFile);
objectFile = 'GeometryObject_Camera_572.mat';
load(objectFile);
fprintf ('Have read the Geometry object from file\n');
roadMask = geom.getRoadMask();

% background
subtractor = BackgroundSubtractor(5, 25, 80);

% detector
modelPath = [CITY_DATA_PATH, 'violajones/models/model1.xml'];
detector = CascadeCarDetector (modelPath);

t = 2;
while 1
    tic
    
    % read image
    frame = frameReader.getNewFrame();
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
    carsFilt = [];
    for k = 1 : length(cars)
        center = cars(k).getCenter(); % [y x]
        if foregroundMask(center(1), center(2))
            carsFilt = [carsFilt cars(k)];
        end
    end
    cars = carsFilt;
    
    % count cars
     cars2 = {};
     for i = 1:length(cars.bbox)
         cars2{i} = CarAppearance(cars.bbox(i, :), frameReader.counter);
         cars2{i}.generateFeature(frame);
     end
    counting = MetricLearner(); % pass necessary arguments to constructor
    count0 = length(detector.detect(im0));  %%%???
    [newCarNumber Match] = counting.processFrame(frameReader.counter, frame, cars2, geom);  % cars is the cell array of the class carappearance, every cell is the carappearance based on every bbox
    count1 = count0 + newCarNumber;    % count1 is the total number of cars for all the frames.
    count0 = count1; 
    
    % output
    tCycle = toc;
    frame_out = frame;
    for j = 1 : length(cars)
        frame_out = cars(j).drawCar(frame_out);
    end
    imshow(frame_out);
    
    fprintf ('frame %d in %f sec \n', t, tCycle);
end
