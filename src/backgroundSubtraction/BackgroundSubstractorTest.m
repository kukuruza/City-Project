% test that the background substraction class works the same way
%   as the original Lynna's code

clear all

run ../subdirPathsSetup.m


%% input and ground truth
videoPath = [CITY_DATA_PATH '2-hours/camera572.avi'];



%% test

frameReader = FrameReaderVideo (videoPath);
subtractor = BackgroundSubtractor (5, 25, 80);

while true
    frame = frameReader.getNewFrame();
    [mask, bboxes] = subtractor.subtract(frame);
    frame_out = subtractor.drawboxes(frame, bboxes);
    %imshow(frame_out);
    maskOut = maskProcess(mask);
  %   subplot(1,2,1),imshow(frame);
  %   subplot(1,2,2),
    imshow(maskOut);
    pause(0.5);
end
