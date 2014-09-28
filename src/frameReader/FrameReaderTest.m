% Test implementations of FrameReader
%
% Press ctrl+c to stop
%

clear all

%frameReader = FrameReaderVideo();
frameReader = FrameReaderImages();
%frameReader = FrameReaderInternet();

while true
    frame = frameReader.getNewFrame();
    if isempty(frame)
        break
    end
    
    imshow(frame)
    pause(0.1)
end
    
