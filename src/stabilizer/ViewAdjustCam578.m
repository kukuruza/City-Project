% Reading the same scene from two different images, from different sources
% and finding if they are separated by a homography
% cam 578

% Setting up the root
run '../rootPathsSetup.m';
run '../subdirPathsSetup.m'

% Images from frames-4pm
rootPath = [CITY_DATA_PATH, 'camdata/cam578/models'];

%Reading two images
image1 = imread(fullfile(rootPath, 'backimage-Jan22-14h.png'));
image2 = imread(fullfile(rootPath, 'backimage-Mar15-10h.png'));

%%%%%%%%%%%%%%%%%%% Manually marking points %%%%%%%%%%%%%%%%%%%
%figure(1); imshow([image1, image2])
%[x, y] = getpts;
% Removing the last point
% x = x(1:end-1); 
% y = y(1:end-1);
% % Adjusting the offset in x
% pts1 = [x(1:2:end), y(1:2:end)];
% pts2 = [x(2:2:end)-size(image1, 2), y(2:2:end)];
% % Saving the points back
% save('points-cam578.mat', 'pts1', 'pts2');
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Computing the homography with these points (RANSAC)
load('points-cam578.mat');
[grouping, bestH] = ransacHomography(pts1', pts2');
fprintf('Consensus: %f \n', sum(grouping)/size(pts1, 1));

warpImage2 = warpH(image2, bestH, size(image1));
homography = bestH;
%save('homography578.mat', 'homography');

% Showing the image pair:
% Left side corresponds to warped frame (observe the two channels are
% aligned - more or less)
%
% Right side correspond to unwarped frame (observe the two channels widely
% differ in the views)

figure(1); imshowpair([warpImage2, image2], [image1, image1], ...
                                        'ColorChannels', 'red-cyan')
