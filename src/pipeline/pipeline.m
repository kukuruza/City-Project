% test pipeline
%
% This file reads images from a directory and processes them one by one,
%   as if they were coming real-time.
%

clear all

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
    foregroundMask = subtractor.subtract(gray);

    % geometry processing mask and bboxes
    foregroundMask = foregroundMask & logical(roadMask);
    bboxes = subtractor.mask2bboxes(foregroundMask);
    %[scales, orientation] = geom.guess(foregroundMask, bboxes);
    
    assert (isempty(bboxes) || size(bboxes,2) == 4);
    %assert (isempty(scale) || isvector(scale));
    %assert (size(bboxes,2) == length(scales) && size(bboxes,2) == length(orientations));
    
    bboxes = expandBboxes (bboxes, ExpandBoxesPerc, im);
    N = size(bboxes,1);
    
%     img_out = subtractor.drawboxes(im, bboxes);
%     imshow(foregroundMask);
%     waitforbuttonpress
    
    % actually detect cars
    cars = [];
    for j = 1 : N
        bbox = bboxes(j,:);
        patch = extractBboxPatch (im, bbox);
        carsInPatch = detector.detect(patch);%, scales(j), orientations(j));
        % bring the bboxes to the absolute coordinate system
        for k = 1 : length(carsInPatch)
            carsInPatch(k).bbox = addOffset2Boxes(int32(carsInPatch(k).bbox), bbox(1:2));
        end
        cars = [cars carsInPatch];
    end
    
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
