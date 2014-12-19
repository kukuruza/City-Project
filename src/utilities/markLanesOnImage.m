% Script to mark points and then detect vanishing points
% Marking 3 points per line; starting from the leftmost lane as seen in the
% image
clear
clc

%Directory and image name (grabbing an image marking lanes, change
%accordindly)

imageDir = '~/CMU/5-camera-for-2-hours/2-min/camera572';
imageName = 'image0000.jpg';
filePath = fullfile(imageDir, imageName);

if(~exist(filePath, 'file'))
   fprintf('Image doesnt exists at %s\n', filePath); 
end

%Reading the image and marking points
image = imread(filePath);
imshow(image)
[xPts, yPts] = getpts;

%Save the points to a file along with other attributes, that can be
%suitably adjusted
%noPointsPerLine = 3;
%noLanes = 5;
%directions = [];

%save 'cam_geometry.mat' 'xPts' 'yPts' 'noPointsPerLine' 'noLanes';
