% Test implementations of FrameReader
%
% Press ctrl+c to stop
%

clear all

% setup data directory
run '../rootPathsSetup.m';


videoPath = [CITY_DATA_PATH, '2-min/camera360.avi'];
frameReader = FrameReaderVideo (videoPath);

imDir = [CITY_DATA_PATH, '2-min/camera360/'];
%frameReader = FrameReaderImages (imDir);

%frameReader = FrameReaderInternet (360);


while true
    tic
    pause(0.1)
    frame = frameReader.getNewFrame();
    if isempty(frame)
        break
    end
    
    imshow(frame)
    toc
end
    
