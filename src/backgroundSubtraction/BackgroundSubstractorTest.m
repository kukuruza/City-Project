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
imagesDir = [CITY_DATA_PATH 'camdata/cam572/2-hours/'];



%% test

frameReader = FrameReaderImages (imagesDir);
subtractor = BackgroundSubtractor();


% background subtraction
subtractor.num_training_frames = 5;
subtractor.initial_variance = 30;

% mask refinement
subtractor.fn_level = 15;
subtractor.fp_level = 1;

% extracting bounding boxes
subtractor.minimum_blob_area = 50;
         

while true
    frame = frameReader.getNewFrame();
    %[mask, bboxes] = subtractor.subtract(frame);
    [mask, bboxes] = subtractor.subtractAndDenoise (frame);
    %bboxes
    frame_out = subtractor.drawboxes(frame, bboxes);
    subplot(1,2,1),imshow(frame_out);
    subplot(1,2,2),imshow(mask);
    pause(0.5);
end
