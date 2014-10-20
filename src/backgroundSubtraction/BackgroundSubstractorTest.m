% test that the background substraction class works the same way
%   as the original Lynna's code
%
% Ctrl+C to interrupt unfortunately


clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% add all scripts to matlab pathdef
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
    subplot(2,2,3),imshow(mask);
    tic
    maskOut = denoiseForegroundMask(mask, 15, 1);
    toc
    subplot(2,2,1),imshow(frame);
    subplot(2,2,2),imshow(maskOut);
    pause(0.5);
end
