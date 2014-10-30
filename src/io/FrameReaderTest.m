% Test implementations of FrameReader
%
% Press ctrl+c to stop
%

clear all


% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% setup data directory
run '../rootPathsSetup.m';

% Change the video path accordingly
% Time stamp path is expected to be of the same name but with .txt
% extension
videoPath = [CITY_DATA_PATH, 'cam572/2-hours-morning/2-hours-morning.avi'];
timeStampPath = strrep(videoPath, '.avi', '.txt');
frameReader = FrameReaderVideo (videoPath, timeStampPath);

%imDir = [CITY_DATA_PATH, '2-min/camera360/'];
%frameReader = FrameReaderImages (imDir);

%frameReader = FrameReaderInternet (572);


while true
    tic
    pause(0.1)
    [frame, timeStamp] = frameReader.getNewFrame();
    if isempty(frame)
        break
    end
    
    % Time Display
    %fprintf('Time (yy mm dd hh:mm:ss): %d %d %d %d %d %f)\n', timeStamp);
    
    imshow(frame)
    toc
end
    
