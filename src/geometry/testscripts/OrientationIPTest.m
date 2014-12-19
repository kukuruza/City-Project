% Unit test for the GeometryEstimator class for orientation map and Inverse
% perspective map (visual test)

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

run ../../rootPathsSetup.m
run ../../subdirPathsSetup.m

% Camera id for the test : 572, 360, 368
cameraId = 572;
imageDir = [CITY_DATA_PATH '2-min/camera', num2str(cameraId)];
imageName = 'image0000.jpg';
filePath = fullfile(imageDir, imageName);

%Reading the image
image = imread(filePath);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Loading the road properties that were manually marked (Pts for the lanes)
matFile = sprintf('Geometry_Camera_%d.mat', cameraId);

geom = GeometryEstimator(image, matFile);
fprintf ('GeometryEstimator: constructor finished\n');

% Geometry object can be simply loaded using the object file
% The object geom will be directly loaded. However, newer functionalities
% might need this object to be created again

%objectFile = sprintf('GeometryObject_Camera_%d.mat', cameraId);
%load(objectFile);
%warning(strcat('Read Geometry object from file, might not be the latest version...' , ...
%   'Update if made changes to GeometryEstimator class'));
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Displaying the orientation map
orientationMap = geom.getOrientationMap();
figure; imagesc(orientationMap.yaw)
figure; imagesc(orientationMap.pitch)

% Displaying the inverse perspective transformation
laneRatio = 0.75;
laneWidth = size(image, 2) * 0.25;
[~, warpedImg] = geom.computeIPTransform(image, laneRatio, laneWidth);
figure; imshow([image, warpedImg]);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%