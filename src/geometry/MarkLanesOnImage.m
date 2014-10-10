% Script to mark points and then detect vanishing points
% Marking 3 points per line; starting from the leftmost lane as seen in the
% image
clear
clc

%Directory and image name (grabbing an image marking lanes, change
%accordindly)

imageDir = '~/CMU/5-camera-for-2-hours/cameraNumber360-part1';
imageName = 'image0.jpg';
filePath = fullfile(imageDir, imageName);

%Reading the image and marking points
image = imread(filePath);
[xPts, yPts] = getpts;

%Save the points to a file along with other attributes, that can be
%suitably adjusted
noPointsPerLine = 3;
noLanes = 5;

save 'cam_geometry.mat' 'xPts' 'yPts' 'noPointsPerLine' 'noLanes';
