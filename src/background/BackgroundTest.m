% test that the background subtraction class works the same way
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
outImagePath = [CITY_DATA_PATH 'testdata/background/result/'];


%% test

frameReader = FrameReaderImages (imagesDir);
background = Background('num_training_frames', 5, ...
                        'initial_variance', 30, ...
                        'fn_level', 15, ...
                        'fp_level', 1, ...
                        'minimum_blob_area', 50);
         
N=0;
while true
    frame = frameReader.getNewFrame();
    %[mask, bboxes] = subtractor.subtract(frame);
    [mask, bboxes] = background.subtract (frame);
    %bboxes
    frame_out = background.drawboxes(frame, bboxes);
    subplot(1,2,1),imshow(frame_out);
    subplot(1,2,2),imshow(mask);
    imname = sprintf('result%d.png',N);
    %imwrite(mask,fullfile(outImagePath,imname));
    pause(0.5);
    N=N+1;
end
