% Test implementations of FrameReader
%
% Press ctrl+c to stop
%

clear all

% setup data directory
run '../rootPathsSetup.m';

%frameReader = FrameReaderVideo();
frameReader = FrameReaderImages(493);
%frameReader = FrameReaderInternet();

while true
    frame = frameReader.getNewFrame();
    if isempty(frame)
        break
    end
    
    imshow(frame)
    pause(0.1)
end
    
