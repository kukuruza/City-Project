% test pipeline
%
% This file reads images from a directory and processes them one by one,
%   as if they were coming real-time.
%

imDir = '/Users/evg/Box Sync/City Project/data/five camera for 2 min/cameraNumber360/';
imNames = dir ([imDir, 'image*.jpg']);

im0 = imread([imDir, imNames(1).name]);

backSubtractor = BackgroundSubtractor(im0);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%Geometry Part
%Currently, takes the initialization image - predicts ground, vertical
%surfaces and sky. This can be used to narrow down the search for
%vehicles

%Constructor
geom = GeometryEstimator();
fprintf('Estimating the 3D geometry of the scene...\n');
[cMaps, cMapNames] = geom.getConfidenceMaps(im0);
%cMaps{1}(:,:,1) = confidence map for ground
%cMaps{1}(:,:,2) = confidence map for vertical surfaces
%cMaps{1}(:,:,3) = confidence map for sky
fprintf('Estimation done :D \n');
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

i = 2;
while 1
    
    % read image
    im = imread([imDir, imNames(i).name]);
    gray = rgb2gray(im);
    
    % subtract backgroubd and return mask
    foregroundMask = backSubtractor.subtract(im);
    
    % morphological operation with foreground mask
    %ROIs = 
    
    % geometry should process the mask
    %[scales, orientation] = geom.guess(foregroundMask, ROIs);
    
    assert (isempty(ROIs) || size(ROIs,1) == 4);
    assert (isempty(scale) || isvector(scale));
    assert (size(ROIs,2) == length(scales) && size(ROIs,2) == length(orientations));
    N = size(ROIs,2);
    
    % actually detect cars
    cars = cell(1,N);
    for j = 1 : N
        roi = ROIs(j,:);
        patch = gray (roi(2) : roi(4), roi(1) : roi(3));
        cars(j) =  detectCar(patch, scales(j), orientations(j));
    end
    
    % HMM processing
    
    
    % counting
    
    i = i + 1;
end