% Reading the same scene from two different images, from different sources
% and finding if they are separated by a homography
% cam 450

% Setting up the root
run '../rootPathsSetup.m';
run '../subdirPathsSetup.m'

% Images from frames-4pm
rootPath = [CITY_DATA_PATH, 'camdata/cam450'];

% Images from video 10-min-sunny.avi
videoPath = fullfile(rootPath, '2pm/10-min-sunny.avi');
stampPath = fullfile(rootPath, '2pm/10-min-sunny.txt');
reader1 = FrameReaderVideo(videoPath, stampPath);

% Frame reader
imagePath = fullfile(rootPath, 'frames-4pm/');
reader2 = FrameReaderImages(imagePath);

noFrames = 1;

% Reading the frames
frame1 = reader1.getNewFrame();
frame2 = reader2.getNewFrame();

%%%%%%%%%%%%%%%%%%% Manually marking points %%%%%%%%%%%%%%%%%%%
% figure(1); imshow([frame1, frame2])
% [x, y] = getpts;
% Adjusting the points
% load('points-cam450.mat');
% ptsV = [x(1:2:end), y(1:2:end)]';
% ptsI = [x(2:2:end) - size(frame1, 2), y(2:2:end)]';
% save('points-cam450.mat', 'ptsI', 'ptsV');
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Computing the homography with these points (RANSAC)
load('points-cam450.mat');
[grouping, bestH] = ransacHomography(ptsI, ptsV);
fprintf('Consensus: %f \n', sum(grouping)/size(ptsV, 2));

warpFrame1 = warpH(frame1, bestH, size(frame1));

% Showing the image pair:
% Left side corresponds to warped frame (observe the two channels are
% aligned - more or less)
%
% Right side correspond to unwarped frame (observe the two channels widely
% differ in the views)

figure(1); imshowpair([warpFrame1, frame1], [frame2, frame2], ...
                                        'ColorChannels', 'red-cyan')