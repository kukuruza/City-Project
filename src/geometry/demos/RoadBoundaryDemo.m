% Script to demo the use of vanishing point detection and boundary
% detection

%clear all;

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script

% Read the videos and get the frames
camId = 572;
videoPath = [CITY_DATA_PATH 'camdata/cam572/5pm/15-mins.avi'];
timesPath = [CITY_DATA_PATH 'camdata/cam572/5pm/15-mins.txt'];
frameReader = FrameReaderVideo (videoPath, timesPath);

objectFile = [CITY_DATA_PATH, 'models/cam572/GeometryObject_Camera_572.mat'];
load(objectFile)

% Add path
addpath(genpath('../vanishpoint/'));

noFrames = 1;
for i = 1:noFrames
    [frame, ~] = frameReader.getNewFrame();
    
    colorImg = imresize(frame, 0.50);
    grayImg = rgb2gray(colorImg);
    outputPath = './';
    numOfValidFiles = i;
    norient = 36;
    
    tic
    % Detecting the vanishingpoint
    [vanishPt, orientationMap] = ...
        geom.detectVanishingPoint(grayImg, colorImg, norient, ...
                                outputPath, numOfValidFiles);
    toc
    
    % Detecting the boundary
    [newVanishPoint, boundaries, displayImg] = ...
        geom.detectRoadBoundary(colorImg, vanishPt, orientationMap, ...
                                outputPath, numOfValidFiles);
    
    fprintf('Vanishing points: (%f , %f) (%f , %f)\nBoundaries : (%f , %f)\n', ...
                    vanishPt(1), vanishPt(2), newVanishPoint(1), newVanishPoint(2), ...
                                boundaries(1), boundaries(2));
    figure(1); imshow(displayImg)
    %figure(2); imagesc(roadImg)
    %pause(0.1)
end