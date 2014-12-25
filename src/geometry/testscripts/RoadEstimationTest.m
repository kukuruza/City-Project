% test pipeline
%
% This file reads images from a directory and processes them one by one,
%   as if they were coming real-time.
%

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% setup all the paths
run ../../rootPathsSetup.m;
run ../../subdirPathsSetup.m;

% input frames
%videoPath = [CITY_DATA_PATH 'camdata/cam572/5pm/15-mins.avi'];
imagePath = [CITY_DATA_PATH '2-min/camera368/'];
%timesPath = [CITY_DATA_PATH 'camdata/cam572/5pm/15-mins.txt'];
%frameReader = FrameReaderVideo (videoPath, timesPath); 
frameReader = FrameReaderImages(imagePath);

% background
background = BackgroundGMM();
return
% geometry
objectFile = '../GeometryObject_Camera_572.mat';
load(objectFile);
fprintf ('Have read the Geometry object from file\n');

roadCameraMap = geom.getCameraRoadMap();

noFrames = 20;
boundaryPath = [CITY_DATA_PATH, 'geometry/vpestimation/cam572/roadBinary/'];
boundaryPath

% Get one frame to compare sizes and scale accordingly
[frame, timeStamp] = frameReader.getNewFrame();

% Estimate the road boundaries along with vanishingpoint using RANSAC
[vanishPoint, boundaryLanes] = geom.estimateRoad(frame, boundaryPath, noFrames);

geom.boundaryLanes = boundaryLanes;
geom.road.vanishPt = vanishPoint';

% Generating the road belief
for t = 1 : 100
    %fprintf('frame %d\n', t);
    tic
    
    % read image
    [frame, timestamp] = frameReader.getNewFrame();
    if isempty(frame), break, end
    gray = rgb2gray(frame);
    % subtract backgroubd and return mask
    % bboxes = N x [x1 y1 width height]
    %foregroundMask = background.subtract(frame, 'denoise', true);

    % geometry processing mask and bboxes
    %foregroundMask = foregroundMask & logical(roadCameraMap);
    foregroundMask = background.subtract(frame) & logical(roadCameraMap);
    
    % Debugging lane detection
    geom.generateRoadBelief(foregroundMask, frame);
    
    tCycle = toc;
    fprintf ('frame %d in %f sec\n', t, tCycle);
end

clear frameWriter frameReader;