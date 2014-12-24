% test that the background subtraction class works the same way
%   as the original Lynna's code
%
% Ctrl+C to interrupt unfortunately


clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% add all scripts to matlab pathdef
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m



%% input and ground truth
imagesDir = [CITY_DATA_PATH 'camdata/cam572/2-hours/'];
outPath = [CITY_DATA_PATH 'testdata/background/demo/cam572-2-hours.avi'];

doWrite = true;


%% test

frameReader = FrameReaderImages (imagesDir);
frameWriter = FrameWriterVideo (outPath, 2, [1 2]);

background = BackgroundGMM('AdaptLearningRate', true, ...
                           'NumTrainingFrames', 50, ...
                           'LearningRate', 0.005, ...
                           'MinimumBackgroundRatio', 0.9, ...
                           'NumGaussians', 2, ...
                           'InitialVariance', 15^2, ...
                           'fn_level', 15, ...
                           'fp_level', 1, ...
                           'minimum_blob_area', 50);

for t = 0 : 10000
    frame = frameReader.getNewFrame();
    mask = background.subtract(frame, 'denoise', false);
    bboxes = background.mask2bboxes(mask);
    frame_out = background.drawboxes(frame, bboxes);
    subplot(1,2,1), imshow(frame_out);
    subplot(1,2,2), imshow(mask);
    imname = sprintf('result%d.png', t);
    if doWrite, frameWriter.writeNextFrame({frame, mask}); end
    %pause(0.5);
end

clear frameWriter frameReader

