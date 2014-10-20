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

camNum = 360;

% expand bboxes from BackgroundSubtractor to feed CarDetector
ExpandBoxesPerc = 0.5;

% input frames
frameReader = FrameReaderImages ([CITY_DATA_PATH '2-min/camera360/']); 
im0 = frameReader.getNewFrame();

% geometry
matFile = [CITY_SRC_PATH 'geometry/Geometry_Camera_360.mat'];
geom = GeometryEstimator(im0, matFile);
roadMask = geom.getRoadMask();

% background
subtractor = BackgroundSubtractor(5, 30);

% detector
modelPath = [CITY_DATA_PATH, 'violajones/models/model1.xml'];
detector = CascadeCarDetector (modelPath);

t = 2;
while 1
    tic
    
    % read image
    im = frameReader.getNewFrame();
    if isempty(im), break, end
    gray = rgb2gray(im);
    
    % subtract backgroubd and return mask
    % bboxes = N x [x1 y1 width height]
    foregroundMask = subtractor.subtractAndDenoise(gray);

    % geometry processing mask and bboxes
    foregroundMask = foregroundMask & logical(roadMask);
    
    % actually detect cars
    cars = detector.detect(im);%, scales(j), orientations(j));
    
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
    
    
%     % output
     tCycle = toc;
%     frame_out = im;
%     for j = 1 : length(cars)
%         frame_out = showCarboxes(frame_out, cars{j});
%     end
%     frame_out = subtractor.drawboxes(frame_out, bboxes);
%     imshow(frame_out);
    
    fprintf ('frame %d in %f sec \n', t, tCycle);

    t = t + 1;
end
