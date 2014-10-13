% Test implementations of FrameReader
%
% Press ctrl+c to stop
%

clear all

% setup data directory
run '../rootPathsSetup.m';

%frameReader = FrameReaderVideo();
%frameReader = FrameReaderImages(493);
frameReader = FrameReaderInternet(360);

while true
    frame = frameReader.getNewFrame();
    if isempty(frame)
        break
    end
    
    imshow(frame)
    pause(1)
end
    
