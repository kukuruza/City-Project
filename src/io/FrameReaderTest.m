% Test implementations of FrameReader
%
% Press ctrl+c to stop
%

clear all

% setup data directory
run '../rootPathsSetup.m';

frameReader = FrameReaderVideo(368);
%frameReader = FrameReaderImages(360);
%frameReader = FrameReaderInternet();

while true
    frame = frameReader.getNewFrame();
    if isempty(frame)
        break
    end
    
    imshow(frame)
    pause(0.1)
end
    
