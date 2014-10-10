% test pipeline
%
% This file reads images from a directory and processes them one by one,
%   as if they were coming real-time.
%

clear all

% setup all the paths
run ../subdirPathsSetup.m;

% percentage for expandoing boxes
ExpandBoxesPerc = 0.2;

frameReader = FrameReaderImages(); 
im0 = frameReader.getNewFrame();

%modelPath = 'voc-dpm-voc-release5.02/VOC2010/car_final.mat';
%detector = CarDetector(modelPath, '2010', 5, -0.5);

subtractor = BackgroundSubtractor(5, 30);

matFile = 'Geometry_Camera_360.mat';
geom = GeometryEstimator(im0, matFile);

t = 2;
while 1
    tic
    
    % read image
    im = frameReader.getNewFrame();
    if isempty(im), break, end
    gray = rgb2gray(im);
    
    % subtract backgroubd and return mask
    % bboxes = N x [x1 y1 width height]
    [foregroundMask, bboxes] = subtractor.subtract(gray);

    % geometry should process the mask
    %[scales, orientation] = geom.guess(foregroundMask, bboxes);
    
    assert (isempty(bboxes) || size(bboxes,2) == 4);
    %assert (isempty(scale) || isvector(scale));
    %assert (size(bboxes,2) == length(scales) && size(bboxes,2) == length(orientations));
    
    bboxes = expandBboxes (bboxes, ExpandBoxesPerc, im);
    N = size(bboxes,1);
    
    % actually detect cars
    cars = [];
    for j = 1 : N
        bbox = bboxes(j,:);
        patch = im (bbox(2) : bbox(4)+bbox(2)-1, bbox(1) : bbox(3)+bbox(1)-1, :);
        carsPatch = detector.detect(patch);%, scales(j), orientations(j));
        % bring the bboxes to the absolute coordinate system
        for k = 1 : length(carsPatch)
            carsPatch{k}.bboxes = addOffset2Boxes(int32(carsPatch{k}.bboxes), bbox(1:2));
        end
        cars = [cars; carsPatch];
    end
    
    % HMM processing
    
    
    % output
    tCycle = toc;
    frame_out = im;
    for j = 1 : length(cars)
        frame_out = showCarboxes(frame_out, cars{j});
    end
    frame_out = subtractor.drawboxes(frame_out, bboxes);
    imshow(frame_out);
    
    fprintf ('frame %d in %f sec \n', t, tCycle);

    t = t + 1;
end
