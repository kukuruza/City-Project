
clear all

run ../subdirPathsSetup.m


%% input and ground truth
videoPath = [CITY_DATA_PATH 'camera360.avi'];



%% test

frameReader = FrameReaderVideo (videoPath);

while true
    frame = frameReader.getNewFrame();
    %imshow(frame_out);
    pause(0.5);
end