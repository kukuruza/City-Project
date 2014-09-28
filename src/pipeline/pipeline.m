% test pipeline
%
% This file reads images from a directory and processes them one by one,
%   as if they were coming real-time.
%

clear all

imDir = '/Users/evg/Box Sync/City Project/data/five camera for 2 min/cameraNumber360/';
imNames = dir ([imDir, 'image*.jpg']);
im0 = imread([imDir, imNames(1).name]);

modelPath = 'voc-dpm-voc-release5.02/VOC2010/car_final.mat';
detector = CarDetector(modelPath, '2010', 5, -0.5);

subtractor = BackgroundSubtractor(5, 30);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%Geometry Part
%Currently, takes the initialization image - predicts ground, vertical
%surfaces and sky. This can be used to narrow down the search for
%vehicles

%Constructor
% geom = GeometryEstimator();
% fprintf('Estimating the 3D geometry of the scene...\n');
% [cMaps, cMapNames] = geom.getConfidenceMaps(im0);
%cMaps{1}(:,:,1) = confidence map for ground
%cMaps{1}(:,:,2) = confidence map for vertical surfaces
%cMaps{1}(:,:,3) = confidence map for sky
% fprintf('Estimation done :D \n');
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

t = 2;
while 1
    tic
    
    % read image
    im = imread([imDir, imNames(t).name]);
    gray = rgb2gray(im);
    
    % subtract backgroubd and return mask
    % ROIs = N x [x1 y1 x2 y2]
    [foregroundMask, ROIs] = subtractor.subtract(gray);

    % geometry should process the mask
    %[scales, orientation] = geom.guess(foregroundMask, ROIs);
    
    assert (isempty(ROIs) || size(ROIs,2) == 4);
    %assert (isempty(scale) || isvector(scale));
    %assert (size(ROIs,2) == length(scales) && size(ROIs,2) == length(orientations));
    N = size(ROIs,1);
    
    % actually detect cars
    cars = [];
    for j = 1 : N
        roi = ROIs(j,:);
        patch = im (roi(2) : roi(4)-1, roi(1) : roi(3)-1, :);
        carsPatch = detector.detect(patch);%, scales(j), orientations(j));
        cars = [cars; carsPatch];
    end
    
    % HMM processing
    
    
    % output
    tCycle = toc;
    fprintf ('frame %d in %f sec \n', t, tCycle);
    frame_out = im;
    %for j = 1 : length(cars)
    %    showCarboxes(frame_out, cars{j}, frame_out);
    %end
    frame_out = subtractor.drawROIs(frame_out, ROIs);
    
    t = t + 1;
end
