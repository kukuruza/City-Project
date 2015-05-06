% Test file to check the Stabilizer class that uses the planar road for
% stabilizing the images, through RANSAC
% Stabilizing the videos using inbuild matlab function

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script

% Setting up the path for the video
rootPath = [CITY_DATA_PATH, 'camdata/cam578/'];
videoPath = fullfile(rootPath, 'Mar12-12h-sunny.avi');
stampPath = fullfile(rootPath, 'Mar12-12h-sunny.txt');

% Frame reader
reader = FrameReaderVideo(videoPath, stampPath);

noFrames = 1000;
[refFrame, ~] = reader.getNewFrame();
corrector = Stabilizer(refFrame);

for i = 1:noFrames
    tic
    [curFrame, ~] = reader.getNewFrame();
    
    if(isempty(curFrame))
       return
    end
    
    % Stabilizing the frame
    stableFrame = corrector.stabilizeFrame(curFrame, 'general');
    %stableFrame = corrector.stabilizeFrame(curFrame);
    
    % Stabilizing the frame just with translation
    %stableFrame = corrector.stabilizeFrame(curFrame, 'translation');
    
    % Debugging through various image displays
    figure(1); imshow([curFrame, refFrame; stableFrame, stableFrame])
    %figure(1); imshowpair([stableFrame, ], [refFrame, ], 'ColorChannels', 'red-cyan');
    %figure(1); imshowpair([stableFrame, curFrame], [refFrame, refFrame], ...
    %                                    'ColorChannels', 'red-cyan');
%    figure(1); imshowpair([stableFrame, curFrame], [refFrame, refFrame], ...
%                                                                'diff');
  
    %pause(0.1)
    toc
end
   
clear reader