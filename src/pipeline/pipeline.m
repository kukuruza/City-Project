% test pipeline
%
% This file reads images from a directory and processes them one by one,
%   as if they were coming real-time.
%

clear all

imDir = '/Users/evg/Box Sync/City Project/data/five camera for 2 min/cameraNumber360/';
imNames = dir ([imDir, 'image*.jpg']);

modelPath = 'voc-dpm-voc-release5.02/VOC2010/car_final.mat';
detector = CarDetector(modelPath, '2010', 5, -0.5);

subtractor = BackgroundSubtractor();

%geom = GeometryEstimator(im0);

i = 1;
while 1
    
    % read image
    im = imread([imDir, imNames(i).name]);
    gray = rgb2gray(im);
    
    % subtract backgroubd and return mask
    [foregroundMask, ROIs] = subtractor.subtract(gray);
    
    % geometry should process the mask
    %[scales, orientation] = geom.guess(foregroundMask, ROIs);
    
    assert (isempty(ROIs) || size(ROIs,1) == 4);
    %assert (isempty(scale) || isvector(scale));
    %assert (size(ROIs,2) == length(scales) && size(ROIs,2) == length(orientations));
    N = size(ROIs,2);
    
    % actually detect cars
    cars = cell(1,N);
    for j = 1 : N
        roi = ROIs(j,:);
        patch = im (roi(2) : roi(4), roi(1) : roi(3));
        cars(j) =  detector.detect(patch);%, scales(j), orientations(j));
    end
    
    % HMM processing
    
    % counting
    
    i = i + 1;
end
