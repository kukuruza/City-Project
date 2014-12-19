% A simple tutorial script to demonstrate the use of Geometry class for
% various functionalities

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

run ../../rootPathsSetup.m
run ../../subdirPathsSetup.m

imageDir = [CITY_DATA_PATH '2-min/camera572'];
imageName = 'image0000.jpg';
filePath = fullfile(imageDir, imageName);

%Reading the image and marking points
image = imread(filePath);

% Loading the road properties that were manually marked (Pts for the lanes)
%matFile = 'Geometry_Camera_368.mat';
%matFile = 'Geometry_Camera_360.mat';
matFile = 'Geometry_Camera_572.mat';
geom = GeometryEstimator(image, matFile);
fprintf ('GeometryEstimator: constructor finished\n');

% Geometry object can be simply loaded using the object file
% The object geom will be directly loaded. However, newer functionalities
% might need this object to be created again
%objectFile = 'GeometryObject_Camera_360.mat';
%load(objectFile);
%warning(strcat('Read Geometry object from file, might not be the latest version...' , ...
%   'Update if made changes to GeometryEstimator class'));

%geom.computeCameraRoadMapWithH();
roadMap = geom.getCameraRoadMap();
%figure; imagesc(roadMap)
% geom.computeHomography();
% 
% % Warping the image
% %figure; imshow([image, warpH(image, geom.homography, size(image))]);
% 
% figure; imshow(image)
% 
% % Debugging the opposite point method
% point = [236; 201];
% line = geom.road.lanes{end}.rightEq;
% oppLine = geom.road.lanes{1}.leftEq;
% H = geom.getOppositePoint(point, line, oppLine);

%figure; imshow([image, warpH(image, H, size(image))]);

% debugging the orientation map
geom.computeOrientationMap();
orientationMap = geom.getOrientationMap();
figure; imagesc(orientationMap.yaw)
%figure; imagesc(orientationMap.pitch);
% Debugging the orientation map computation
%geom.computeOrientationMap();
%orientMap = geom.getOrientationMap();
%imshow(orientMap)