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
videoDir = [CITY_DATA_PATH 'camdata/cam572/5pm/'];
videoPath = [videoDir '15-mins.avi'];
timesPath = [videoDir '15-mins.txt'];
frameReader = FrameReaderVideo (videoPath, timesPath); 

% geometry
objectFile = fullfile(CITY_DATA_PATH, 'models/cam572', ...
                                'GeometryObject_Camera_572.mat');
load(objectFile);
fprintf ('Have read the Geometry object from file\n');
%roadCameraMap = geom.getCameraRoadMap();

% Estimate the road boundaries along with vanishingpoint using RANSAC
boundaryPath = [CITY_DATA_PATH, 'testdata/geometry/roadBinary/cam572/']; 
[frame, timestamp] = frameReader.getNewFrame(); % Get one frame
noTrainingFrames = 10;
[vanishPoint, boundaryLanes, cameraMask, ~] = ...
            geom.estimateRoad(frame, boundaryPath, noTrainingFrames);

% Saving computed results
geom.boundaryLanes = boundaryLanes;
geom.road.vanishPt = vanishPoint';
geom.imageSize = size(frame);
roadCameraMap = cameraMask;

% background
load ([CITY_DATA_PATH 'models/cam572/backgroundGMM.mat']);
pretrainBackground (background, [CITY_DATA_PATH 'camdata/cam572/5pm/']);

for t = 1 : 100
    fprintf('frame %d\n', t);
    tic
    
    % read image
    [frame, timestamp] = frameReader.getNewFrame();
    if isempty(frame), break, end
    
    % subtract backgroubd and return mask
    % bboxes = N x [x1 y1 width height]
    %foregroundMask = background.subtract(frame_ghost, 'denoise', true);

    % geometry processing mask and bboxes
    foregroundMask = background.subtract(frame);
    %foregroundMask = foregroundMask & logical(roadCameraMap);
    
    % Geometry processing goes here (independent of the pipeline)
    figure(1); imshow(foregroundMask)
    
    tCycle = toc;
    fprintf ('frame %d in %f sec \n \n', t, tCycle);    
    pause(0.1)
end

clear frameWriter frameReader

